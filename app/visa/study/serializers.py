from rest_framework import serializers
from .models import StudyVisaApplication


class StudyVisaApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudyVisaApplication
        fields = [
            'id',
            'applicant',
            'passport_number',
            'country',
            'institution',
            'course_of_study',
            'application_date',
            'status',
            'notes',
        ]
        read_only_fields = ['application_date', 'status']

    def create(self, validated_data):
        # status is handled in model save() if not provided
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

