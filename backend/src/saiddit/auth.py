"""Session-based authentication routes."""
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth

User = get_user_model()

router = Router()


class RegisterIn(Schema):
    username: str
    email: str
    password: str


class LoginIn(Schema):
    username: str
    password: str


class UserOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str


@router.post('/csrf', response={204: None}, auth=None)
def csrf(request):
    """Set the csrftoken cookie so the frontend can echo it on unsafe requests."""
    # get_token flags the token as used, so CsrfViewMiddleware attaches the
    # cookie to this response.
    get_token(request)
    return 204, None


@router.post('/register', response={201: UserOut}, auth=None)
def register(request, payload: RegisterIn):
    """Create a new account and start a session for it."""
    if User.objects.filter(username__iexact=payload.username).exists():
        raise ValidationError({'username': 'That username is already taken.'})

    try:
        validate_password(payload.password)
    except ValidationError as exc:
        # Re-raise against the field so the global handler can attribute it.
        raise ValidationError({'password': exc.messages})

    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )

    login(request, user)
    return 201, user


@router.post('/login', response={200: UserOut}, auth=None)
def login_view(request, payload: LoginIn):
    """Verify credentials and start a session."""
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        raise HttpError(401, 'Invalid username or password.')

    login(request, user)
    return 200, user


@router.post('/logout', response={204: None}, auth=django_auth)
@csrf_exempt
def logout_view(request):
    """End the current session.

    Exempt from CSRF: django-ninja picks the flag up off the view and tells
    SessionAuth to skip the check. Ending a session is not a state change an
    attacker gains anything from, and the request still needs a valid session
    cookie to do anything at all.
    """
    logout(request)
    return 204, None


@router.get('/me', response={200: UserOut}, auth=django_auth)
def me(request):
    """Return the currently authenticated user."""
    return 200, request.user
