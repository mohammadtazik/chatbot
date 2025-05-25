from django.http import HttpResponse


def home(request):
    return HttpResponse("✅ Chatbot API is running!")
