from django.shortcuts import render
from django.http import HttpResponseRedirect

# Import Models
from .models import Course, Enrollment, Question, Choice, Submission

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging


# Get an instance of a logger
logger = logging.getLogger(__name__)


# ============================================================
# USER REGISTRATION
# ============================================================

def registration_request(request):
    context = {}

    if request.method == 'GET':
        return render(
            request,
            'onlinecourse/user_registration_bootstrap.html',
            context
        )

    elif request.method == 'POST':

        # Get registration information
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']

        user_exist = False

        try:
            User.objects.get(username=username)
            user_exist = True

        except User.DoesNotExist:
            logger.error("New user")

        if not user_exist:

            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )

            login(request, user)

            return redirect("onlinecourse:index")

        else:

            context['message'] = "User already exists."

            return render(
                request,
                'onlinecourse/user_registration_bootstrap.html',
                context
            )


# ============================================================
# USER LOGIN
# ============================================================

def login_request(request):

    context = {}

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['psw']

        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('onlinecourse:index')

        else:

            context['message'] = "Invalid username or password."

            return render(
                request,
                'onlinecourse/user_login_bootstrap.html',
                context
            )

    else:

        return render(
            request,
            'onlinecourse/user_login_bootstrap.html',
            context
        )


# ============================================================
# USER LOGOUT
# ============================================================

def logout_request(request):

    logout(request)

    return redirect('onlinecourse:index')


# ============================================================
# CHECK COURSE ENROLLMENT
# ============================================================

def check_if_enrolled(user, course):

    is_enrolled = False

    if user.id is not None:

        num_results = Enrollment.objects.filter(
            user=user,
            course=course
        ).count()

        if num_results > 0:
            is_enrolled = True

    return is_enrolled


# ============================================================
# COURSE LIST VIEW
# ============================================================

class CourseListView(generic.ListView):

    template_name = 'onlinecourse/course_list_bootstrap.html'

    context_object_name = 'course_list'

    def get_queryset(self):

        user = self.request.user

        courses = Course.objects.order_by(
            '-total_enrollment'
        )[:10]

        for course in courses:

            if user.is_authenticated:

                course.is_enrolled = check_if_enrolled(
                    user,
                    course
                )

        return courses


# ============================================================
# COURSE DETAIL VIEW
# ============================================================

class CourseDetailView(generic.DetailView):

    model = Course

    template_name = 'onlinecourse/course_detail_bootstrap.html'

    def get_object(self, queryset=None):

        course = super().get_object(queryset)

        if self.request.user.is_authenticated:

            course.is_enrolled = check_if_enrolled(
                self.request.user,
                course
            )

        return course


# ============================================================
# ENROLL IN COURSE
# ============================================================

def enroll(request, course_id):

    course = get_object_or_404(
        Course,
        pk=course_id
    )

    user = request.user

    is_enrolled = check_if_enrolled(
        user,
        course
    )

    if not is_enrolled and user.is_authenticated:

        # Create enrollment
        Enrollment.objects.create(
            user=user,
            course=course,
            mode='honor'
        )

        course.total_enrollment += 1

        course.save()

    return HttpResponseRedirect(
        reverse(
            viewname='onlinecourse:course_details',
            args=(course.id,)
        )
    )


# ============================================================
# EXTRACT ANSWERS FROM EXAM FORM
# ============================================================

def extract_answers(request):

    submitted_answers = []

    for key in request.POST:

        if key.startswith('choice'):

            value = request.POST[key]

            choice_id = int(value)

            submitted_answers.append(choice_id)

    return submitted_answers


# ============================================================
# SUBMIT EXAM
# ============================================================

def submit(request, course_id):

    # Only process POST requests
    if request.method == 'POST':

        # Get course
        course = get_object_or_404(
            Course,
            pk=course_id
        )

        # Get logged-in user
        user = request.user

        # User must be logged in
        if not user.is_authenticated:

            return redirect(
                'onlinecourse:login'
            )

        # Get enrollment for this user and course
        enrollment = get_object_or_404(
            Enrollment,
            user=user,
            course=course
        )

        # Create submission
        submission = Submission.objects.create(
            enrollment=enrollment
        )

        # Get selected answers
        selected_choice_ids = extract_answers(
            request
        )

        # Add selected choices to submission
        for choice_id in selected_choice_ids:

            choice = get_object_or_404(
                Choice,
                pk=choice_id
            )

            submission.choices.add(choice)

        submission.save()

        # Redirect to result page
        return redirect(
            'onlinecourse:exam_result',
            course_id=course.id,
            submission_id=submission.id
        )

    # If request is not POST
    return redirect(
        'onlinecourse:course_details',
        pk=course_id
    )


# ============================================================
# SHOW EXAM RESULT
# ============================================================

def show_exam_result(
    request,
    course_id,
    submission_id
):

    # Get course
    course = get_object_or_404(
        Course,
        pk=course_id
    )

    # Get submission
    submission = get_object_or_404(
        Submission,
        pk=submission_id
    )

    # Get selected choices
    selected_choices = submission.choices.all()

    # Get all questions belonging to course
    questions = course.question_set.all()

    total_questions = questions.count()

    correct_questions = 0

    # Check every question
    for question in questions:

        # IDs of correct answers
        correct_choice_ids = set(
            question.choice_set.filter(
                is_correct=True
            ).values_list(
                'id',
                flat=True
            )
        )

        # IDs selected by learner for this question
        selected_choice_ids = set(
            selected_choices.filter(
                question=question
            ).values_list(
                'id',
                flat=True
            )
        )

        # Award score only when selected answer
        # exactly matches the correct answer
        if (
            correct_choice_ids
            and
            correct_choice_ids == selected_choice_ids
        ):

            correct_questions += 1

    # Calculate percentage score
    if total_questions > 0:

        grade = round(
            (correct_questions / total_questions) * 100,
            2
        )

    else:

        grade = 0

    # Store score in submission
    submission.score = grade

    submission.save()

    # Data sent to result template
    context = {

        'course': course,

        'submission': submission,

        'choices': selected_choices,

        'grade': grade,

        'user': request.user
    }

    return render(
        request,
        'onlinecourse/exam_result_bootstrap.html',
        context
    )