# Data migration: Create default tenant and migrate existing users

from django.db import migrations


def create_default_tenant_and_migrate_users(apps, schema_editor):
    """Create default tenant and migrate all existing users."""
    Tenant = apps.get_model('accounts', 'Tenant')
    User = apps.get_model('accounts', 'User')

    # Create default tenant
    default_tenant = Tenant.objects.create(
        name="Default",
        slug="default",
        plan="PRO",  # Give PRO to existing users
        max_bots=10,
        max_messages_per_month=50000
    )

    # Migrate all existing users to default tenant
    User.objects.filter(tenant__isnull=True).update(tenant=default_tenant)


def reverse_tenant_migration(apps, schema_editor):
    """Reverse: Delete default tenant and set tenant to null."""
    Tenant = apps.get_model('accounts', 'Tenant')
    User = apps.get_model('accounts', 'User')

    # Set tenant to null for users of default tenant
    User.objects.filter(tenant__slug='default').update(tenant=None)

    # Delete default tenant
    Tenant.objects.filter(slug='default').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_tenant_model'),
    ]

    operations = [
        migrations.RunPython(
            create_default_tenant_and_migrate_users,
            reverse_tenant_migration
        ),
    ]
