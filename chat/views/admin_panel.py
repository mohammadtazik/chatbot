import bcrypt
from bson import ObjectId
from chat.models import User
from django.contrib import messages
from django.shortcuts import redirect, render


# ✅ ویو ورود ادمین با session
def admin_login_view(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        password = request.POST.get("password")

        user = User.objects(phone=phone, is_admin=True).first()
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            request.session["admin_user_id"] = str(user.id)
            return redirect("user_admin_panel")
        else:
            messages.error(
                request, "اطلاعات وارد شده معتبر نیست یا دسترسی ادمین ندارید."
            )

    return render(request, "admin_login.html")


def admin_logout_view(request):
    request.session.flush()
    return redirect("admin_login")


# ✅ ویو پنل مدیریت کاربران
def user_admin_panel(request):
    admin_id = request.session.get("admin_user_id")
    if not admin_id:
        return redirect("admin_login")

    user = User.objects(id=ObjectId(admin_id), is_admin=True).first()
    if not user:
        return redirect("admin_login")

    query = request.GET.get("q", "")
    users = User.objects()
    if query:
        users = users.filter(
            __raw__={
                "$or": [
                    {"username": {"$regex": query, "$options": "i"}},
                    {"phone": {"$regex": query, "$options": "i"}},
                ]
            }
        )
    users = users.order_by("-created_at")
    return render(request, "admin/user_list.html", {"users": users, "query": query})


# ✅ فعال/مسدود کردن کاربر
def toggle_ban_user(request, user_id):
    admin_id = request.session.get("admin_user_id")
    if not admin_id:
        return redirect("admin_login")

    user = User.objects(id=user_id).first()
    if user:
        user.is_banned = not user.is_banned
        user.save()
    return redirect("user_admin_panel")


# ✅ حذف کاربر
def delete_user(request, user_id):
    admin_id = request.session.get("admin_user_id")
    if not admin_id:
        return redirect("admin_login")

    user = User.objects(id=user_id).first()
    if user:
        user.delete()
    return redirect("user_admin_panel")
