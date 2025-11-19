from rest_framework import serializers
from .models import (
    CVProfile,
    CVEducation,
    CVExperience,
    CVCertification,
    CVSkill,
    CVLanguage,
    CVPublication,
)


class CVEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVEducation
        fields = [
            "id",
            "institution",
            "degree",
            "field",
            "start_year",
            "end_year",
            "grade",
            "description",
        ]


class CVExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVExperience
        fields = [
            "id",
            "organization",
            "position",
            "start_month",
            "start_year",
            "end_month",
            "end_year",
            "location",
            "description",
            "current",
        ]


class CVCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVCertification
        fields = [
            "id",
            "name",
            "issuer",
            "issue_month",
            "issue_year",
            "description",
        ]


class CVSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVSkill
        fields = [
            "id",
            "skill",
        ]


class CVLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVLanguage
        fields = [
            "id",
            "name",
            "proficiency",
        ]


class CVPublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVPublication
        fields = [
            "id",
            "title",
            "journal",
            "year",
            "link",
            "description",
        ]


class CVProfileSerializer(serializers.ModelSerializer):
    education = CVEducationSerializer(many=True, read_only=True)
    experience = CVExperienceSerializer(many=True, read_only=True)
    certifications = CVCertificationSerializer(many=True, read_only=True)
    skills = CVSkillSerializer(many=True, read_only=True)
    languages = CVLanguageSerializer(many=True, read_only=True)
    publications = CVPublicationSerializer(many=True, read_only=True)

    class Meta:
        model = CVProfile
        fields = [
            "id",
            "user",
            "summary",
            "photo",
            "created_at",
            "updated_at",
            "education",
            "experience",
            "certifications",
            "skills",
            "languages",
            "publications",
        ]
