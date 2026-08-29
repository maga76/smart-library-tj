import uuid
import json
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import get_language
from django.views import View
from .models import AIChatMessage
from .services import generate_dono_response


class ChatView(LoginRequiredMixin, View):
    def get(self, request):
        session_id = request.session.get('ai_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['ai_session_id'] = session_id

        messages_list = AIChatMessage.objects.filter(session_id=session_id).order_by('created_at')

        # If no message yet, generate initial welcome greeting
        if not messages_list.exists():
            current_lang = get_language() or 'ru'
            greeting = generate_dono_response('салом' if current_lang in ['tg', 'tk', 'tj'] else 'привет', current_lang, request.user)
            welcome_msg = AIChatMessage.objects.create(
                session_id=session_id,
                role='assistant',
                content=greeting,
                language=current_lang,
            )
            messages_list = [welcome_msg]

        return render(request, 'ai_assistant/chat.html', {
            'messages': messages_list,
            'session_id': session_id,
        })


class ChatSendView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        content = data.get('message', '').strip()
        if not content:
            return JsonResponse({'error': 'Empty message'}, status=400)

        session_id = request.session.get('ai_session_id', str(uuid.uuid4()))
        request.session['ai_session_id'] = session_id

        current_lang = get_language() or 'ru'

        # Save User message
        AIChatMessage.objects.create(
            session_id=session_id,
            role='user',
            content=content,
            language=current_lang,
        )

        # Generate Dono response
        response_text = generate_dono_response(content, language=current_lang, user=request.user)

        # Save Assistant response
        AIChatMessage.objects.create(
            session_id=session_id,
            role='assistant',
            content=response_text,
            language=current_lang,
        )

        return JsonResponse({
            'status': 'success',
            'response': response_text,
            'session_id': session_id,
        })
