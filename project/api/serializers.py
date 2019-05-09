from rest_framework import serializers

from api.forms import UpdateProfileImage
from api.models import Civi, Thread, Account, Category, CiviImage
from utils.constants import CIVI_TYPES

WRITE_ONLY = {'write_only': True}


class AccountSerializer(serializers.ModelSerializer):
    """
    General seralizer for a single model instance of a user account
    """
    email = serializers.EmailField(allow_blank=False, write_only=True, source='user.email', required=False)
    username = serializers.ReadOnlyField(source='user.username')

    profile_image = serializers.ImageField(write_only=True, allow_empty_file=False, required=False)
    profile_image_url = serializers.ReadOnlyField()
    profile_image_thumb_url = serializers.ReadOnlyField()

    address = serializers.CharField(allow_blank=True, write_only=True)
    zip_code = serializers.CharField(allow_blank=True, write_only=True)

    longitude = serializers.FloatField(max_value=180, min_value=-180, write_only=True, required=False)
    latitude = serializers.FloatField(max_value=90, min_value=-90, write_only=True, required=False)
    location = serializers.ReadOnlyField()

    class Meta:
        model = Account
        fields = ('username', 'first_name', 'last_name', 'about_me', 'location','email',
        'address', 'city', 'state', 'zip_code', 'country', 'longitude', 'latitude',
        'profile_image', 'profile_image_url', 'profile_image_thumb_url')

        extra_kwargs = {
            'email': WRITE_ONLY,
            'city': WRITE_ONLY,
            'state': WRITE_ONLY,
            'country': WRITE_ONLY,
        }

    def validate_profile_image(self, value):
        request = self.context['request']
        validation_form = UpdateProfileImage(request.POST, request.FILES)

        if validation_form.is_valid():
            # Clean up previous images
            account = Account.objects.get(user=request.user)
            account.profile_image.delete()
            account.profile_image_thumb.delete()

            return validation_form.clean_profile_image()
        else:
            raise serializers.ValidationError(validation_form.errors['profile_image'])


class AccountListSerializer(serializers.ModelSerializer):
    """
    Seralizer for multiple account model instances
    """
    username = serializers.ReadOnlyField(source='user.username')
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()

    profile_image_thumb_url = serializers.ReadOnlyField()

    class Meta:
        model = Account
        fields = ('username', 'first_name', 'last_name', 'profile_image_thumb_url',)


class CiviImageSerializer(serializers.ModelSerializer):
    image_url = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()

    class Meta:
        model = CiviImage
        fields = ('civi', 'title', 'image_url', 'created')


class CiviSerializer(serializers.ModelSerializer):
    author = AccountListSerializer()
    type = serializers.ChoiceField(choices=CIVI_TYPES, source='c_type')
    images = serializers.SlugRelatedField(many=True, read_only=True, slug_field='image_url')
    created = serializers.ReadOnlyField(source='created_date_str')
    score = serializers.SerializerMethodField()

    class Meta:
        model = Civi
        fields = ('id', 'thread', 'type', 'title', 'body', 'author', 'created', 'last_modified',
        'votes', 'images', 'linked_civis', 'responses', 'score')

    def get_score(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        if user.is_anonymous():
            return 0
        else:
            account = Account.objects.get(user=user)
            return obj.score(account.id)


class CiviListSerializer(serializers.ModelSerializer):
    author = AccountListSerializer()
    type = serializers.CharField(source='c_type')
    created = serializers.ReadOnlyField(source='created_date_str')

    class Meta:
        model = Civi
        fields = ('id', 'thread', 'type', 'title', 'body', 'author', 'created')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class ThreadSerializer(serializers.ModelSerializer):
    author = AccountListSerializer(required=False)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    civis = serializers.HyperlinkedRelatedField(many=True, view_name='civi-detail', read_only=True)
    created = serializers.ReadOnlyField(source='created_date_str')
    image = serializers.ImageField(write_only=True, allow_empty_file=False, required=False)

    num_views = serializers.ReadOnlyField()
    num_civis = serializers.ReadOnlyField()
    num_solutions = serializers.ReadOnlyField()

    class Meta:
        model = Thread
        fields = ('id', 'title', 'summary', 'author', 'image_url', 'civis', 'image',
        'created', 'level', 'state', 'is_draft', 'category',
        'num_views', 'num_civis', 'num_solutions')
