from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self):
        context = {
            'title': 'Об авторе проекта'
        }
        return context


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self):
        context = {
            'title': 'Технологии'
        }
        return context
