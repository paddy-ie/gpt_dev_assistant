from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def voice_upload(request):
    if request.method == 'POST':
        # Placeholder for voice-to-text integration
        transcript = "Transcribed text would go here."
        return render(request, 'voice/result.html', {'transcript': transcript})
    return render(request, 'voice/upload.html')