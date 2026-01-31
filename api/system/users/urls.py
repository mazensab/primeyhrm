from django.urls import path
from api.system import users_actions

urlpatterns = [

    path(
        "actions/reset-password/",
        users_actions.reset_user_password,
        name="system_user_reset_password",
    ),

    path(
        "actions/toggle-status/",
        users_actions.toggle_user_status,
        name="system_user_toggle_status",
    ),

    path(
        "actions/change-role/",
        users_actions.change_user_role,
        name="system_user_change_role",
    ),

    path(
        "actions/delete/",
        users_actions.delete_user,
        name="system_user_delete",
    ),
]
