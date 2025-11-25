import hashlib

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
    column_list = ['id', 'name', 'username', 'role', 'storage_limit_gb', 'is_locked']
    column_filters = ['role', 'is_locked']
    column_searchable_list = ['name', 'username']
    column_exclude_list = ['password', 'avatar', 'created_date']
    column_labels = {
        'name': 'Họ tên',
        'username': 'Tài khoản',
        'role': 'Vai trò',
        'is_locked': 'Khóa',
        'storage_limit_gb': 'Giới hạn (GB)'
    }

    # Cấu hình form (Create/Edit view)
    form_columns = ['name', 'username', 'password', 'role', 'storage_limit_gb', 'is_locked']
    form_excluded_columns = ['avatar', 'created_date', 'files', 'folders']
    can_edit = True
    can_create = True
    can_delete = True

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password = str(hashlib.md5(form.password.data.encode('utf-8')).hexdigest())

        if is_created and not model.storage_limit_gb:
            model.storage_limit_gb = 15

        if model.id == current_user.id and model.is_locked:
            raise ValueError("Bạn không thể tự khóa tài khoản Admin của mình!")

    def get_list(self, page, sort_field, sort_desc, search, filters, execute=True):
        def role_formatter(view, context, model, name):
            if model.role == UserRole.ADMIN:
                return '<span class="badge bg-danger">Quản trị viên</span>'
            return '<span class="badge bg-secondary">Người dùng</span>'

        self.column_formatters['role'] = role_formatter

        def lock_formatter(view, context, model, name):
            if model.is_locked:
                return '<span class="badge bg-warning text-dark">Đã khóa</span>'
            return '<span class="badge bg-success">Hoạt động</span>'

        self.column_formatters['is_locked'] = lock_formatter

        return super().get_list(page, sort_field, sort_desc, search, filters, execute)


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
admin.add_view(UserView(User, db.session, name="Quản lý Người dùng", endpoint='user_management_view'))
admin.add_view(BillingView(BillingPackage, db.session, name="Quản lý Gói cước"))
admin.add_view(MyLogoutView(name="Đăng xuất"))