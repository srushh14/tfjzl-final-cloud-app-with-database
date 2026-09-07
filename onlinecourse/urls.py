from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


app_name = 'onlinecourse'


urlpatterns = [

    # Course list / home page
    path(
        '',
        views.CourseListView.as_view(),
        name='index'
    ),

    # User registration
    path(
        'registration/',
        views.registration_request,
        name='registration'
    ),

    # User login
    path(
        'login/',
        views.login_request,
        name='login'
    ),

    # User logout
    path(
        'logout/',
        views.logout_request,
        name='logout'
    ),

    # Course detail
    # Example: /onlinecourse/5/
    path(
        '<int:pk>/',
        views.CourseDetailView.as_view(),
        name='course_details'
    ),

    # Course enrollment
    # Example: /onlinecourse/5/enroll/
    path(
        '<int:course_id>/enroll/',
        views.enroll,
        name='enroll'
    ),

    # Submit exam
    # Example: /onlinecourse/5/submit/
    path(
        '<int:course_id>/submit/',
        views.submit,
        name='submit'
    ),

    # Show exam result
    # Example: /onlinecourse/course/5/submission/2/result/
    path(
        'course/<int:course_id>/submission/<int:submission_id>/result/',
        views.show_exam_result,
        name='exam_result'
    ),

] + static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)