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
    education = CVEducationSerializer(many=True)
    experience = CVExperienceSerializer(many=True)
    certifications = CVCertificationSerializer(many=True)
    skills = CVSkillSerializer(many=True)
    languages = CVLanguageSerializer(many=True)
    publications = CVPublicationSerializer(many=True)

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

    def create(self, validated_data):
        # Extract nested data
        education_data = validated_data.pop('education', [])
        experience_data = validated_data.pop('experience', [])
        certifications_data = validated_data.pop('certifications', [])
        skills_data = validated_data.pop('skills', [])
        languages_data = validated_data.pop('languages', [])
        publications_data = validated_data.pop('publications', [])

        # Create the main profile
        cv_profile = CVProfile.objects.create(**validated_data)

        # Bulk create for each nested set. Use related_name + set attribute, not profile arg.
        # Education
        for edu in education_data:
            cv_profile.education.create(**edu)
        # Experience
        for exp in experience_data:
            cv_profile.experience.create(**exp)
        # Certifications
        for cert in certifications_data:
            cv_profile.certifications.create(**cert)
        # Skills
        for skill in skills_data:
            cv_profile.skills.create(**skill)
        # Languages
        for lang in languages_data:
            cv_profile.languages.create(**lang)
        # Publications
        for pub in publications_data:
            cv_profile.publications.create(**pub)

        return cv_profile

    def update(self, instance, validated_data):
        # Extract nested data
        education_data = validated_data.pop('education', [])
        experience_data = validated_data.pop('experience', [])
        certifications_data = validated_data.pop('certifications', [])
        skills_data = validated_data.pop('skills', [])
        languages_data = validated_data.pop('languages', [])
        publications_data = validated_data.pop('publications', [])

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Helper to update nested relations: deletes all old, creates new using related_name
        def update_nested(related_manager, data_list):
            related_manager.all().delete()
            for item in data_list:
                related_manager.create(**item)

        update_nested(instance.education, education_data)
        update_nested(instance.experience, experience_data)
        update_nested(instance.certifications, certifications_data)
        update_nested(instance.skills, skills_data)
        update_nested(instance.languages, languages_data)
        update_nested(instance.publications, publications_data)

        return instance
