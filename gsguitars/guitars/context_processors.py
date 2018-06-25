from .models import ContactPage


#def guitars(request):
#    return {
#        'guitars': Guitar.objects.all()
#    }
#

def guitars(request):
    return {
        'contact_info': ContactPage.objects.first()
    }
