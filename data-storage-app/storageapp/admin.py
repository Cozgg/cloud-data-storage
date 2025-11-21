from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, request, render_template
from storageapp import admin, db, dao
from storageapp.models import User, BillingPackage, UserRole


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class UserView(AuthenticatedModelView):
    column_list = ['id', 'name', 'username', 'role', 'is_locked']
    column_filters = ['role', 'is_locked']
    column_searchable_list = ['name', 'username']
    can_edit = True
    can_create = True


class BillingView(AuthenticatedModelView):
    column_list = ['id', 'name', 'price', 'storage_limit_gb']
    can_edit = True
    can_create = True
    can_delete = True


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN
    @expose('/')
    def index(self):
        user_count = dao.get_user_count()
        total_storage = dao.get_total_storage_used()
        return self.render('admin/index.html',
                           user_count=user_count,
                           total_storage=total_storage)


class MyLogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


# Thêm các view vào admin
admin.add_view(UserView(User, db.session, name="Quản lý Người dùng"))
admin.add_view(BillingView(BillingPackage, db.session, name="Quản lý Gói cước"))
admin.add_view(MyLogoutView(name="Đăng xuất"))