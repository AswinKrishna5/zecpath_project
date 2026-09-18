from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CustomUser,EmployerProfile,Job,CandidateProfile,Application
from rest_framework.test import APIClient
# Create your tests here.

class CustomUserTest(TestCase):
    def test_candidate_user_creation(self):
        user=CustomUser.objects.create_user(username="testcandidate",email="testcandidate@gmail.com",password="testcandidate1@123",role="CANDIDATE")
        self.assertEqual(user.role,"CANDIDATE")
        self.assertEqual(user.email,"testcandidate@gmail.com")
        self.assertTrue(user.check_password("testcandidate1@123"))

    def test_user_login(self):
        CustomUser.objects.create_user(username="loginuser",email="loginuser@gmail.com",password="loginuser1@123",role="CANDIDATE")
        client=APIClient()
        response=client.post("/api/auth/login/",{"username":"loginuser","password":"loginuser1@123"},format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_employer_can_access_application_list(self):
        employer_user=CustomUser.objects.create_user(username="testemployer",email="testemployer@example.com",password="TestPassword123", role="EMPLOYER")
        employer_profile=EmployerProfile.objects.create(user=employer_user,company_name="test company")
        job = Job.objects.create(employer=employer_profile,title="Python Developer",description="Python backend development",skills="Python, Django",
            experience="1 year",salary_min=30000,salary_max=50000,location="Kerala",job_type=Job.JobType.FULL_TIME,status=Job.Status.ACTIVE)
        client=APIClient()
        login_response=client.post("/api/auth/login/",{
            "username": "testemployer",
            "password": "TestPassword123"},format="json")
        access_token=login_response.data["access"]
        client.credentials( HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response=client.get(f"/api/auth/employer/jobs/{job.id}/applications/")
        self.assertEqual(response.status_code,200)

    def test_employer_can_create_job(self):
        employer_user=CustomUser.objects.create_user(username="jobemployer",email="jobemployer@example.com",password="TestPassword123",role="EMPLOYER")
        employer_profile=EmployerProfile.objects.create(user=employer_user,company_name="job test company")
        job=Job.objects.create(employer=employer_profile,title="Django Developer",description="Backend development using Django",skills="Python, Django, SQL",
            experience="1 year",salary_min=30000,salary_max=50000,location="Kerala",job_type=Job.JobType.FULL_TIME,status=Job.Status.ACTIVE)
        self.assertIsNotNone(job.id)
        self.assertEqual(job.title,"Django Developer")
        self.assertEqual(job.employer, employer_profile)
        self.assertEqual(job.status, Job.Status.ACTIVE)

    def test_candidate_can_apply_for_job(self):

        candidate_user = CustomUser.objects.create_user(username="testcandidateapply",email="testcandidateapply@example.com",password="TestPassword123",role="CANDIDATE")
        candidate_profile = CandidateProfile.objects.create(user=candidate_user,full_name="Test Candidate",skills="Python, Django",education="BCA",experience="1 year")
        resume_file = SimpleUploadedFile("resume.pdf",b"Test resume content",content_type="application/pdf")
        candidate_profile.resume = resume_file
        candidate_profile.resume.save("resume.pdf",resume_file,save=True)
        employer_user = CustomUser.objects.create_user(username="applicationemployer",email="applicationemployer@example.com",password="TestPassword123",role="EMPLOYER")
        employer_profile = EmployerProfile.objects.create(user=employer_user,company_name="Application Test Company")
        job = Job.objects.create(employer=employer_profile,title="Python Developer",description="Python backend development",skills="Python, Django",
            experience="1 year",salary_min=30000,salary_max=50000,location="Kerala",job_type=Job.JobType.FULL_TIME,status=Job.Status.ACTIVE)
        client = APIClient()
        login_response = client.post("/api/auth/login/",
        {
            "username": "testcandidateapply",
            "password": "TestPassword123"},format="json")
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data["access"]
        client.credentials( HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.post(f"/api/auth/jobs/{job.id}/apply/")
        self.assertEqual(response.status_code, 201)
        application = Application.objects.get(candidate=candidate_profile,job=job)
        self.assertEqual(application.status,Application.Status.APPLIED)
        self.assertIsNotNone(application.ats_score)

    def test_candidate_cannot_apply_twice(self):

        candidate_user = CustomUser.objects.create_user(username="duplicatecandidate",email="duplicatecandidate@example.com",password="TestPassword123",role="CANDIDATE")
        candidate_profile = CandidateProfile.objects.create(user=candidate_user,full_name="Duplicate Candidate",skills="Python, Django",education="BCA",experience="1 year")
        resume_file = SimpleUploadedFile("resume.pdf",b"Test resume content",content_type="application/pdf")
        candidate_profile.resume.save("resume.pdf",resume_file,save=True)
        employer_user = CustomUser.objects.create_user(username="duplicateemployer",email="duplicateemployer@example.com",password="TestPassword123",role="EMPLOYER")
        employer_profile = EmployerProfile.objects.create(user=employer_user,company_name="Duplicate Test Company")
        job = Job.objects.create(employer=employer_profile,title="Backend Developer", description="Backend development",skills="Python, Django",
            experience="1 year",salary_min=30000,salary_max=50000,location="Kerala",job_type=Job.JobType.FULL_TIME,status=Job.Status.ACTIVE)
        client = APIClient()
        login_response = client.post("/api/auth/login/",
            {
                "username": "duplicatecandidate",
                "password": "TestPassword123"
            },format="json")
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        first_response = client.post( f"/api/auth/jobs/{job.id}/apply/")
        self.assertEqual(first_response.status_code, 201)
        second_response = client.post(f"/api/auth/jobs/{job.id}/apply/")
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(Application.objects.filter(candidate=candidate_profile,job=job).count(),1)

    def test_employer_cannot_apply_for_job(self):

        employer_user = CustomUser.objects.create_user(username="notcandidate",email="notcandidate@example.com",password="TestPassword123",role="EMPLOYER")
        employer_profile = EmployerProfile.objects.create(user=employer_user,company_name="Role Test Company")
        job = Job.objects.create(employer=employer_profile,title="Python Developer",description="Python backend development",
            skills="Python, Django",experience="1 year",salary_min=30000,salary_max=50000,location="Kerala",job_type=Job.JobType.FULL_TIME,
            status=Job.Status.ACTIVE)
        client = APIClient()
        login_response = client.post("/api/auth/login/",
            {
                "username": "notcandidate",
                "password": "TestPassword123"
            },format="json")
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.post(f"/api/auth/jobs/{job.id}/apply/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Application.objects.filter(job=job).count(), 0)

    def test_employer_cannot_access_another_employers_applications(self):

        employer_one = CustomUser.objects.create_user(username="employerone",email="employerone@example.com",password="TestPassword123",role="EMPLOYER")
        employer_one_profile = EmployerProfile.objects.create(user=employer_one, company_name="Company One")
        job = Job.objects.create(employer=employer_one_profile,title="Python Developer",description="Python backend development",
            skills="Python, Django",experience="1 year",salary_min=30000,salary_max=50000,location="Kerala",
            job_type=Job.JobType.FULL_TIME,status=Job.Status.ACTIVE)
        employer_two = CustomUser.objects.create_user(username="employertwo",email="employertwo@example.com",password="TestPassword123", role="EMPLOYER")
        EmployerProfile.objects.create(user=employer_two,company_name="Company Two")
        client = APIClient()
        login_response = client.post( "/api/auth/login/",
            {
                "username": "employertwo",
                "password": "TestPassword123"
            },format="json")
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data["access"]
        client.credentials( HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.get( f"/api/auth/employer/jobs/{job.id}/applications/")
        self.assertEqual(response.status_code, 404)

    def test_candidate_cannot_access_another_candidate_profile(self):

        candidate_one = CustomUser.objects.create_user(username="candidateone",email="candidateone@example.com",password="TestPassword123",role="CANDIDATE")
        candidate_two = CustomUser.objects.create_user(username="candidatetwo",email="candidatetwo@example.com",password="TestPassword123",role="CANDIDATE")
        profile_one = CandidateProfile.objects.create(user=candidate_one, full_name="Candidate One", phone="9876543210",
            skills="Python, Django",education="BCA",experience="1 year")
        profile_two = CandidateProfile.objects.create(user=candidate_two,full_name="Candidate Two",phone="9123456780",
            skills="Java, Spring",education="MCA",experience="2 years")
        client = APIClient()
        login_response = client.post("/api/auth/login/",
            {
                "username": "candidateone",
                "password": "TestPassword123"
            },format="json")
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.get(f"/api/auth/candidate-profile/?user_id={candidate_two.id}" )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( response.data["id"], profile_one.id)
        self.assertNotEqual(response.data["id"],profile_two.id )
        self.assertNotEqual( response.data["full_name"],"Candidate Two")

    def test_invalid_resume_file_type(self):

        candidate_user = CustomUser.objects.create_user(username="filecandidate", email="filecandidate@example.com",password="TestPassword123",role="CANDIDATE")
        client = APIClient()
        login_response = client.post("/api/auth/login/",
            {
                "username": "filecandidate",
                "password": "TestPassword123"
            }, format="json" )
        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        malicious_file = SimpleUploadedFile("malicious.exe",b"fake executable content",content_type="application/octet-stream")
        response = client.post("/api/auth/candidate-profile/",
            {
                "full_name": "File Test Candidate",
                "phone": "9876543210",
                "skills": "Python",
                "education": "BCA",
                "experience": "1 year",
                "resume": malicious_file
            },format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(CandidateProfile.objects.filter(user=candidate_user).exists() )