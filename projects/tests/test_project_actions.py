import json

from django.test import TestCase
from django.urls import reverse

from users.models import User
from projects.models import Project


class ProjectActionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="ownerpass",
            name="Owner",
            surname="One",
        )
        self.participant = User.objects.create_user(
            email="participant@example.com",
            password="participantpass",
            name="Participant",
            surname="User",
        )
        self.project = Project.objects.create(
            name="Test project",
            owner=self.owner,
        )

    def test_project_detail_sets_csrf_cookie(self):
        response = self.client.login(username=self.participant.email, password="participantpass")
        self.assertTrue(response)

        response = self.client.get(
            reverse("projects:project_detail", kwargs={"project_id": self.project.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

    def test_toggle_participation_for_authenticated_user(self):
        self.client.login(username=self.participant.email, password="participantpass")
        url = reverse("projects:toggle_participation", kwargs={"project_id": self.project.id})
        response = self.client.post(url, content_type="application/json", data=json.dumps({}))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "participant": True})
        self.assertTrue(self.project.participants.filter(pk=self.participant.pk).exists())

        response = self.client.post(url, content_type="application/json", data=json.dumps({}))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "participant": False})
        self.assertFalse(self.project.participants.filter(pk=self.participant.pk).exists())

    def test_complete_project_only_by_owner(self):
        self.client.login(username=self.participant.email, password="participantpass")
        url = reverse("projects:complete_project", kwargs={"project_id": self.project.id})
        response = self.client.post(url, content_type="application/json", data=json.dumps({}))

        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            response.content,
            {"status": "error", "error": "Only owner can complete project"},
        )

        self.client.logout()
        self.client.login(username=self.owner.email, password="ownerpass")
        response = self.client.post(url, content_type="application/json", data=json.dumps({}))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "project_status": "closed"})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")
