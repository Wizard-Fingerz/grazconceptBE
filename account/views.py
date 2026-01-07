from account.models import User
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Q
from rest_framework.permissions import IsAdminUser
from account.client.serializers import ClientSerializer
from account.client.models import Client
from app.views import CustomPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from app.flight.models import FlightBooking
from app.citizenship.investment.models import Investment, InvestmentPlan
from app.help_center.support_ticket.models import SupportTicket
from wallet.loan.models import LoanApplication, LoanOffer
import calendar
from app.visa.study.models import StudyVisaApplication
from app.visa.work.offers.models import WorkVisaApplication
from wallet.transactions.models import WalletTransaction

from .serializers import (
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)
from .models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny


# Why is there no referred_by in my serializer?
# Actually, it IS in your UserRegistrationSerializer. Your serializer:
#   - accepts it (it's in the fields list and as a serializer.CharField).
#   - but in your .create() method of the serializer, you ignore it and don't use it to set on the User.
#   - So, that's why you pull it in the view and apply it to the model *after* creating the user instance, right before final .save().
# This is so you don't set the referred_by on your User model via the serializer itself but assign it directly on the model. Both approaches can work, but currently you chose to handle assignment in the view outside the serializer (for maybe validation or business logic control).
#
# Main point: There **is** a "referred_by" field in your UserRegistrationSerializer and your view expects clients to POST it as normal.

class SignUpView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={201: openapi.Response(
            'Created', UserRegistrationSerializer)},
    )
    def post(self, request):
        data = request.data.copy()
        # Ensure referred_by from request is sent to serializer (and not blanked out)
        # This way, the serializer receives what the client sent, whether present or not
        print(data)
        serializer = UserRegistrationSerializer(data=data)
        print(serializer)
        if serializer.is_valid():
            user = serializer.save()
            # The serializer already handles referred_by if client sent it;
            # if you still want to post-process (e.g., strip/validate), do it here:
            if "referred_by" in request.data:
                user.referred_by = request.data.get("referred_by", "")
                user.save()

            # Issue JWT tokens after registration
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return Response(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "referred_by": user.referred_by,
                    "user_type": user.user_type.term if user.user_type else None,
                    "access": access_token,
                    "refresh": refresh_token,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["user_type"] = user.user_type.term if user.user_type else None
        return token

    def validate(self, attrs):
        # Replace username with email for authentication
        attrs["username"] = attrs.get("email")
        return super().validate(attrs)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class PasswordResetRequestView(APIView):
    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer, responses={
            200: openapi.Response("OK")}
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{user.pk}/{token}/"
            send_mail(
                "Password Reset",
                f"Click the link to reset your password: {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except UserModel.DoesNotExist:
            pass  # Don't reveal if email exists
        return Response(
            {"message": "If the email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

        # GetMyRefeerees endpoint: returns all users referred by the authenticated user


class GetMyRefeereesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get referees from User model (those whose 'referred_by' = this user's custom_id)
        user_referees = User.objects.filter(referred_by=user.custom_id)
        # Get referees from Client model (those whose 'referred_by' = this user's custom_id)
        client_referees = Client.objects.filter(referred_by=user.custom_id)

        # Combine both querysets as a list, tagging them for serialization
        combined = (
            [{'type': 'user', 'instance': u} for u in user_referees] +
            [{'type': 'client', 'instance': c} for c in client_referees]
        )

        # Sort combined by created_date descending, assuming both models have this field,
        # if not, fallback as-is
        try:
            combined.sort(key=lambda x: getattr(
                x['instance'], 'created_date', None), reverse=True)
        except Exception:
            pass

        paginator = CustomPagination()
        paginated_combined = paginator.paginate_queryset(combined, request)

        # Serialize keeping type info
        results = []
        for item in paginated_combined:
            if item['type'] == 'user':
                # Use context to pass request for serializer if necessary
                data = UserSerializer(item['instance'], context={
                                      'request': request}).data
                data['referee_type'] = 'user'
            else:
                # Force country field (if Country instance) to string in the output, if needed
                client_instance = item['instance']
                client_data = ClientSerializer(client_instance, context={
                                               'request': request}).data
                # Country is already handled as string by ClientSerializer
                client_data['referee_type'] = 'client'
                data = client_data
            results.append(data)

        # Ensure the response is a DRF Response (already paginated)
        return paginator.get_paginated_response(results)

# Admin dashboard analytics view for backend API (to power the frontend dashboard)

class AdminDashboardAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        

        now = timezone.now()

        # Users
        users_total = User.objects.count()

        # Revenue: sum up successful WalletTransactions with status 'successful' and amount > 0
        revenue_total = WalletTransaction.objects.filter(
            status='successful', amount__gt=0
        ).aggregate(amount_sum=Sum('amount'))['amount_sum'] or 0

        # Applications (active)
        applications_active = (
            StudyVisaApplication.objects.count()
            + WorkVisaApplication.objects.count()
        )

        # Approvals pending 
        approvals_pending = (
            StudyVisaApplication.objects.filter(
                status__term='pending').count()
            + WorkVisaApplication.objects.filter(status__term='pending').count()
        )

        # Staff count (not deleted)
        staff_count = User.objects.filter(
            is_staff=True, is_deleted=False
        ).count()

        # Health percent (mock or real)
        health_percent = 99

        # Service stats
        study_visa_count = StudyVisaApplication.objects.count()
        work_visa_count = WorkVisaApplication.objects.count()

        # Flight and Loan stats
        travel_count = FlightBooking.objects.count()

        # Loans statistics
        loans_count = LoanApplication.objects.count()
        # Optionally more loan stats
        loans_active = LoanApplication.objects.filter(
            status__term__in=['Pending', 'Approved']
        ).count()
        total_loan_amount = LoanApplication.objects.aggregate(
            amount_sum=Sum('amount')
        )['amount_sum'] or 0

        # Investment stats
        total_investments = Investment.objects.count()
        total_investors = Investment.objects.values('investor').distinct().count()
        total_roi = Investment.objects.aggregate(total_roi=Sum('roi_amount'))['total_roi'] or 0
        total_amt_invested = Investment.objects.aggregate(amt=Sum('amount'))['amt'] or 0

        # Plan breakdown
        plan_breakdown = []
        for plan in InvestmentPlan.objects.all():
            plan_count = plan.investments.count()
            plan_breakdown.append({
                'plan_name': plan.name,
                'plan_count': plan_count,
                'plan_color': plan.color,
                'total_amount': plan.investments.aggregate(a=Sum('amount'))['a'] or 0,
            })

        # Loan breakdown
        loan_breakdown = []
        for offer in LoanOffer.objects.filter(is_active=True):
            this_loan_count = offer.applications.count()
            this_loan_amount = offer.applications.aggregate(a=Sum('amount'))['a'] or 0
            loan_breakdown.append({
                'loan_name': offer.name,
                'loan_type': str(offer.loan_type),
                'offer_id': offer.id,
                'offer_currency': offer.currency,
                'offer_interest_rate': float(offer.interest_rate),
                'offer_max_amount': float(offer.max_amount),
                'loan_count': this_loan_count,
                'loan_amount': float(this_loan_amount) if this_loan_amount else 0,
            })

        # Analytics per month (last 6 calendar months)
        analytics_data = []
        months_back = 6
        base_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for i in range(months_back):
            m = (base_month.month - months_back + i + 1)
            y = base_month.year
            while m <= 0:
                m += 12
                y -= 1
            month_start = base_month.replace(year=y, month=m, day=1)
            if m == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1)

            users = User.objects.filter(
                is_deleted=False, created_date__gte=month_start, created_date__lt=month_end
            ).count()

            revenue = WalletTransaction.objects.filter(
                status='successful', amount__gt=0,
                created_at__gte=month_start, created_at__lt=month_end
            ).aggregate(amount_sum=Sum('amount'))['amount_sum'] or 0

            applications = (
                StudyVisaApplication.objects.filter(
                    submitted_at__gte=month_start,
                    submitted_at__lt=month_end
                ).count() +
                WorkVisaApplication.objects.filter(
                    submitted_at__gte=month_start,
                    submitted_at__lt=month_end,
                ).count()
            )

            flights = FlightBooking.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()

            investment_count = Investment.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            investment_value = Investment.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).aggregate(val=Sum('amount'))['val'] or 0

            # Loans this month
            loan_count_this_month = LoanApplication.objects.filter(
                created_at__gte=month_start, created_at__lt=month_end
            ).count()
            loan_amount_this_month = LoanApplication.objects.filter(
                created_at__gte=month_start, created_at__lt=month_end
            ).aggregate(val=Sum('amount'))['val'] or 0

            month_label = month_start.strftime('%b')
            analytics_data.append({
                "month": month_label,
                "Users": users,
                "Revenue": revenue,
                "Applications": applications,
                "Flights": flights,
                "Investments": investment_count,
                "InvestmentAmount": investment_value,
                "Loans": loan_count_this_month,
                "LoanAmount": float(loan_amount_this_month) if loan_amount_this_month else 0,
            })

        # System status (mock or use monitoring system)
        status_info = [
            {"label": "API", "status": "Operational", "color": "success", "value": 100},
            {"label": "Database", "status": "Healthy", "color": "success", "value": 99},
            {"label": "Payment Gateway", "status": "Operational", "color": "success", "value": 100},
            {"label": "Email Service", "status": "Operational", "color": "success", "value": 98},
            {"label": "Storage", "status": "Warning: 85% full", "color": "warning", "value": 85},
        ]

        # Recent activities: now includes support tickets and loan activities
        recent_activities = []

        # New users (last 2)
        for u in User.objects.order_by('-created_date')[:2]:
            timestamp = ""
            try:
                if u.created_date:
                    timestamp = u.created_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"user-{u.pk}",
                "type": "user",
                "description": "New user registered",
                "timestamp": timestamp,
                "user": getattr(u, "full_name", str(u)),
            })

        # New study visa applications (last 1)
        for app in StudyVisaApplication.objects.order_by('-submitted_at')[:1]:
            timestamp = ""
            try:
                if app.submitted_at:
                    timestamp = app.submitted_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"studyvisa-{app.pk}",
                "type": "application",
                "description": "Study visa application submitted",
                "timestamp": timestamp,
                "user": str(app.user) if hasattr(app, "user") else "",
            })

        # New investments (last 1)
        for inv in Investment.objects.order_by('-created_at')[:1]:
            timestamp = ""
            try:
                if inv.created_at:
                    timestamp = inv.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"invest-{inv.pk}",
                "type": "investment",
                "description": f"New investment in {inv.plan.name}",
                "timestamp": timestamp,
                "user": str(inv.investor),
            })

        # Latest successful wallet transactions (last 1)
        for tx in WalletTransaction.objects.filter(status='successful').order_by('-created_at')[:1]:
            timestamp = ""
            try:
                if tx.created_at:
                    timestamp = tx.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"payment-{tx.pk}",
                "type": "payment",
                "description": "Payment processed",
                "timestamp": timestamp,
                "user": str(tx.user) if hasattr(tx, "user") else "",
            })

        # Latest flight bookings (last 1)
        for book in FlightBooking.objects.order_by('-created_at')[:1]:
            timestamp = ""
            try:
                if book.created_at:
                    timestamp = book.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            client_str = str(book.client) if hasattr(book, "client") else ""
            try:
                user_name = book.client.full_name
            except Exception:
                user_name = client_str
            recent_activities.append({
                "id": f"flight-{book.pk}",
                "type": "flight",
                "description": "Flight booking created",
                "timestamp": timestamp,
                "user": user_name,
            })

        # NEW: Latest loan applications (last 1)
        for loan_app in LoanApplication.objects.order_by('-created_at')[:1]:
            timestamp = ""
            try:
                if loan_app.created_at:
                    timestamp = loan_app.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"loanapp-{loan_app.pk}",
                "type": "loan_application",
                "description": f"Loan application for {loan_app.loan_offer.name}",
                "timestamp": timestamp,
                "user": str(loan_app.user) if hasattr(loan_app, "user") else "",
            })

        # NEW: Latest loan repayments (last 1)
        from wallet.loan.models import LoanRepayment
        for repay in LoanRepayment.objects.order_by('-created_at')[:1]:
            timestamp = ""
            try:
                if repay.created_at:
                    timestamp = repay.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"loanrepay-{repay.pk}",
                "type": "loan_repayment",
                "description": f"Loan repayment of {repay.amount} {repay.currency} for Loan #{repay.loan_application.id}",
                "timestamp": timestamp,
                "user": str(repay.user) if hasattr(repay, "user") else "",
            })

        # Latest support ticket created (last 1)
        ticket = SupportTicket.objects.order_by('-created_at').first()
        if ticket:
            timestamp = ""
            try:
                if ticket.created_at:
                    timestamp = ticket.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"ticket-{ticket.pk}",
                "type": "support_ticket",
                "description": "Support ticket created",
                "timestamp": timestamp,
                "user": str(ticket.user) if hasattr(ticket, "user") else "",
            })

        # Latest support ticket message (last 1, user or support reply)
        from app.help_center.support_ticket.models import SupportTicketMessage
        msg = SupportTicketMessage.objects.order_by('-timestamp').first()
        if msg:
            timestamp = ""
            try:
                if msg.timestamp:
                    timestamp = msg.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                timestamp = ""
            recent_activities.append({
                "id": f"stmsg-{msg.pk}",
                "type": "support_ticket_message",
                "description": (
                    "Support replied"
                    if msg.sender == SupportTicketMessage.SENDER_SUPPORT
                    else "User replied"
                ),
                "timestamp": timestamp,
                "user": str(msg.ticket.user) if hasattr(msg.ticket, "user") else "",
            })

        # Order descending by timestamp, take top 7 (because more activities with loans)
        def to_sort_key(x):
            try:
                return timezone.datetime.strptime(x["timestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except Exception:
                return timezone.now()
        recent_activities = sorted(
            recent_activities, key=lambda x: to_sort_key(x), reverse=True
        )[:7]

        result = {
            "metrics": {
                "users_total": users_total,
                "revenue_total": revenue_total,
                "applications_active": applications_active,
                "approvals_pending": approvals_pending,
                "staff_count": staff_count,
                "health_percent": health_percent,
                "investment_total": total_investments,
                "amount_invested": float(total_amt_invested),
                "roi_total": float(total_roi),
                "investor_total": total_investors,
                "loans_total": loans_count,
                "loans_active": loans_active,
                "loan_amount_total": float(total_loan_amount) if total_loan_amount else 0,
            },
            "service_stats": {
                "study_visa": study_visa_count,
                "work_visa": work_visa_count,
                "travel": travel_count,
                "loans": loans_count,
                "investments": total_investments,
            },
            "investment_breakdown": plan_breakdown,
            "loan_breakdown": loan_breakdown,
            "status_info": status_info,
            "recent_activities": recent_activities,
            "analytics_data": analytics_data,
        }
        return Response(result)

# Admin analytics and report endpoint: provides dashboard analytics for the AdminAnalytics React view.
# Route suggestion: /api/admin/analytics/ (GET)

from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models.functions import TruncDate
import datetime

class AdminAnalyticsReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Returns the analytics report for frontend AdminAnalytics component.
        Accepts optional ?period= param: '7days', '30days', '90days', '1year' (default: 30days)
        """
        period = request.query_params.get("period", "30days").lower()
        now = timezone.now()
        if period == "7days":
            start_date = now - datetime.timedelta(days=7)
        elif period == "90days":
            start_date = now - datetime.timedelta(days=90)
        elif period == "1year":
            start_date = now - datetime.timedelta(days=365)
        else:
            start_date = now - datetime.timedelta(days=30)

        # Key metrics
        revenue_total = (
            WalletTransaction.objects.filter(
                status='successful',
                amount__gt=0,
                created_at__gte=start_date
            )
            .aggregate(s=Sum('amount'))['s'] or 0
        )
        new_users = (
            User.objects.filter(created_date__gte=start_date)
            .count()
        )
        applications_count = (
            StudyVisaApplication.objects.filter(submitted_at__gte=start_date).count()
            + WorkVisaApplication.objects.filter(submitted_at__gte=start_date).count()
        )
        # Growth rate: e.g., percent new users versus previous period
        prev_new_users = (
            User.objects.filter(
                created_date__gte=start_date - (start_date - now + datetime.timedelta(days=1)),
                created_date__lt=start_date,
            ).count()
        )
        growth_rate = 0.0
        if prev_new_users > 0:
            growth_rate = round(100 * (new_users - prev_new_users) / prev_new_users, 2)
        elif new_users > 0:
            growth_rate = 100.0

        # Revenue Trend for line chart (sum per date, last N days)
        revenue_trend_qs = (
            WalletTransaction.objects.filter(
                status='successful',
                amount__gt=0,
                created_at__gte=start_date,
            )
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(value=Sum('amount'))
            .order_by('day')
        )
        revenue_trend = [
            {"date": d['day'].strftime('%Y-%m-%d'), "value": float(d['value'] or 0)}
            for d in revenue_trend_qs
        ]

        # User growth trend (new users per week, up to 6 past intervals)
        user_growth_qs = (
            User.objects.filter(created_date__gte=start_date)
            .annotate(day=TruncDate('created_date'))
            .values('day')
            .annotate(users=Count('id'))
            .order_by('day')
        )
        user_growth = [
            {"date": d['day'].strftime('%Y-%m-%d'), "users": d['users']}
            for d in user_growth_qs
        ]

        # Application Distribution - Pie: by channel/source if available, or Study/Work visa for demo
        application_pie_data = [
            {
                "name": "Study Visa",
                "value": StudyVisaApplication.objects.filter(submitted_at__gte=start_date).count(),
            },
            {
                "name": "Work Visa",
                "value": WorkVisaApplication.objects.filter(submitted_at__gte=start_date).count(),
            }
        ]
        # Optionally: add more channels if you track them

        # Service Analytics (dummy categories, for demo pie)
        service_analytics = [
            {"name": "Payment", "value": WalletTransaction.objects.filter(
                created_at__gte=start_date, status='successful').count()},
            {"name": "KYC", "value": User.objects.filter(kyc_status='approved', created_date__gte=start_date).count() if hasattr(User, 'kyc_status') else 0},
            {"name": "Loan", "value": LoanApplication.objects.filter(created_at__gte=start_date).count()},
            {"name": "Reporting", "value": SupportTicket.objects.filter(created_at__gte=start_date).count()},
        ]

        # Top Performing Services (used for left pie in lower box): can sort above by value desc
        top_services = sorted(service_analytics, key=lambda x: x["value"], reverse=True)

        # User Demographics: age distribution (demo, only if User model has 'dob')
        age_groups = {
            "18-24": 0,
            "25-34": 0,
            "35-44": 0,
            "45+": 0,
        }
        if hasattr(User, 'dob'):
            # Only count if User model has date-of-birth field
            qs = User.objects.filter(dob__isnull=False, created_date__gte=start_date)
            for user in qs:
                try:
                    age = (now.date() - user.dob).days // 365
                    if 18 <= age <= 24:
                        age_groups["18-24"] += 1
                    elif 25 <= age <= 34:
                        age_groups["25-34"] += 1
                    elif 35 <= age <= 44:
                        age_groups["35-44"] += 1
                    elif age >= 45:
                        age_groups["45+"] += 1
                except Exception:
                    pass
        user_demographics = [{"name": k, "value": v} for k, v in age_groups.items()]

        return Response({
            "metrics": {
                "revenue_total": float(revenue_total),
                "new_users": new_users,
                "applications": applications_count,
                "growth_rate": f"{growth_rate:.2f}%",
            },
            "revenue_trend": revenue_trend,
            "user_growth": user_growth,
            "application_distribution": application_pie_data,
            "service_analytics": service_analytics,
            "top_services": top_services,
            "user_demographics": user_demographics,
            # For chart demo, keep field structure like in React `demoLineData` etc.
        })

