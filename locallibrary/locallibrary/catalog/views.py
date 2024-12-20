from .models import Book
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from .forms import RenewBookForm
from django.shortcuts import render
from .models import BookInstance
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.conf import settings
from .forms import SecretQuestionForm
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.crypto import get_random_string
from .forms import ResetPasswordForm

def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    is_librarian = request.user.is_authenticated and request.user.groups.filter(name='Librarians').exists()
    authors = Author.objects.all()

    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(
        request,
        'catalog/index.html',
        context={'num_books': num_books, 'num_instances': num_instances, 'num_instances_available': num_instances_available, 'num_authors': num_authors,
                 'num_visits': num_visits,  'is_librarian': is_librarian, 'author_list': authors},
    )

class BookListView(generic.ListView):
    model = Book
    template_name = 'catalog/book_list.html'  # Убедитесь, что шаблон существует
    context_object_name = 'book_list'  # Используемое имя для списка книг в шаблоне

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Проверяем, является ли пользователь аутентифицированным и входит ли он в группу 'Librarians'
        context['is_librarian'] = self.request.user.is_authenticated and self.request.user.groups.filter(
            name='Librarians').exists()
        return context

class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'catalog/book_detail.html'  # Убедитесь, что шаблон существует
    context_object_name = 'book'  # Имя переменной, которая будет передана в шаблон

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_librarian'] = self.request.user.is_authenticated and self.request.user.groups.filter(
            name='Librarians').exists()
        return context

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_librarian'] = self.request.user.is_authenticated and self.request.user.groups.filter(
            name='Librarians').exists()
        return context


class AuthorListView(generic.ListView):
    model = Author
    template_name = 'catalog/author_list.html'  # Шаблон для отображения списка авторов
    context_object_name = 'author_list'  # Имя переменной, которая будет использоваться в шаблоне

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_librarian'] = self.request.user.groups.filter(name='Librarians').exists()
        return context

class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'catalog/author_detail.html'  # Шаблон для отображения информации об авторе
    context_object_name = 'author'  # Имя переменной, которая будет использоваться в шаблоне

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Проверяем, является ли пользователь аутентифицированным и входит ли он в группу 'Librarians'
        context['is_librarian'] = self.request.user.is_authenticated and self.request.user.groups.filter(
            name='Librarians').exists()
        return context




class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')



class AllLoanedBooksListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    """
    Представление, которое показывает все книги, взятые в аренду, с именами заёмщиков.
    Доступно только библиотекарям.
    """
    model = BookInstance
    template_name = 'catalog/all_loaned_books.html'
    context_object_name = 'bookinstances'  # Название переменной, доступной в шаблоне

    def get_queryset(self):
        """Фильтруем все книги, которые находятся в статусе 'on loan'."""
        return BookInstance.objects.filter(status='o').order_by('due_back')

    def test_func(self):
        """Проверяем, является ли пользователь библиотекарем."""
        return self.request.user.groups.filter(name='Librarians').exists()

    def get_context_data(self, **kwargs):
        """Добавляем информацию о том, является ли пользователь библиотекарем."""
        context = super().get_context_data(**kwargs)
        context['is_librarian'] = self.request.user.groups.filter(name='Librarians').exists()
        return context




@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-loaned-books') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})

@login_required
def all_loaned_books(request):
    # Получаем все книги на прокате
    bookinstances = BookInstance.objects.filter(status='o').order_by('due_back')

    # Проверяем, является ли пользователь библиотекарем
    is_librarian = request.user.groups.filter(name='Librarians').exists()

    # Передаем информацию в контекст шаблона
    return render(request, 'catalog/all_loaned_books.html', {
        'bookinstances': bookinstances,
        'is_librarian': is_librarian
    })

class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '12/10/2016',}

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    template_name = 'catalog/author_form.html'
    success_url = reverse_lazy('author-list')


class AuthorDelete(DeleteView):
    model = Author
    template_name = 'catalog/author_confirm_delete.html'
    success_url = reverse_lazy('author-list')

class BookCreate(CreateView):
    model = Book
    fields = '__all__'  # Все поля модели Book будут отображаться в форме
    initial = {'isbn': '0000000000000'}  # Пример для начального значения поля (опционально)
    template_name = 'catalog/book_form.html'
    success_url = reverse_lazy('book_list')  # Путь, куда пользователь будет перенаправлен после успешного создания

class BookUpdate(UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre']  # Поля, которые будут доступны для редактирования
    template_name = 'catalog/book_form.html'  # Шаблон, который будет использоваться для отображения формы
    success_url = reverse_lazy('book_list')  # Путь, куда пользователь будет перенаправлен после успешного обновления

class BookDelete(DeleteView):
    model = Book
    template_name = 'catalog/book_confirm_delete.html'  # Шаблон для подтверждения удаления
    success_url = reverse_lazy('book_list')  # Путь, куда пользователь будет перенаправлен после успешного удаления


def reset_password_view(request):
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            secret_answer = form.cleaned_data['secret_answer']

            user = User.objects.filter(username=username).first()

            if user:
                # Получаем профиль пользователя и проверяем секретный ответ
                profile = user.profile
                if profile.secret_answer == secret_answer:
                    # Генерация нового пароля
                    new_password = get_random_string(length=8)

                    # Обновляем пароль пользователя
                    user.set_password(new_password)
                    user.save()

                    # Отображаем новый пароль на экране
                    return HttpResponse(f"Ваш новый пароль: {new_password}")
                else:
                    return HttpResponse("Неверный ответ на секретный вопрос.")
            else:
                return HttpResponse("Пользователь не найден.")
    else:
        form = ResetPasswordForm()

    return render(request, 'catalog/forgot-password.html', {'form': form})


class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'  # Укажите путь к вашему шаблону
    authentication_form = AuthenticationForm  # Стандартная форма аутентификации

    def form_invalid(self, form):
        # Если форма неправильная, можем добавить сообщения об ошибках
        messages.error(self.request, _('Invalid username or password.'))
        return super().form_invalid(form)