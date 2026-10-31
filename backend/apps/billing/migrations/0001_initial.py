import django.db.models.deletion
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        ('subscriptions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingFailure',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subscription_id', models.CharField(db_index=True, max_length=64)),
                ('subscription_number', models.CharField(blank=True, max_length=64)),
                ('period_start', models.DateField(blank=True, null=True)),
                ('period_end', models.DateField(blank=True, null=True)),
                ('error_message', models.TextField()),
                ('stack_trace', models.TextField(blank=True)),
                ('resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InvoiceSequence',
            fields=[
                ('year', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('last_number', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Invoice Sequence',
                'verbose_name_plural': 'Invoice Sequences',
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('invoice_number', models.CharField(max_length=50, unique=True)),
                ('subscription_id', models.CharField(blank=True, db_index=True, max_length=64)),
                ('subscription_number', models.CharField(blank=True, max_length=64)),
                ('customer_name', models.CharField(blank=True, max_length=255)),
                ('customer_email', models.EmailField(blank=True, max_length=254)),
                ('billing_address', models.TextField(blank=True)),
                ('period_start', models.DateField(blank=True, null=True)),
                ('period_end', models.DateField(blank=True, null=True)),
                ('issue_date', models.DateField()),
                ('due_date', models.DateField()),
                ('service_period_start', models.DateField(blank=True, null=True)),
                ('service_period_end', models.DateField(blank=True, null=True)),
                ('subtotal', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('discount_total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('tax_total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('total', models.DecimalField(decimal_places=2, max_digits=14)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('outstanding_balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ('partially_paid', 'Partially Paid'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('pdf_path', models.CharField(blank=True, max_length=255)),
                ('email_sent_at', models.DateTimeField(blank=True, null=True)),
                ('email_attempts', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invoices', to='customers.customer')),
                ('sent_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('subscription_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='subscriptions.subscription')),
            ],
            options={
                'ordering': ['-issue_date', '-created_at'],
                'permissions': [('send_invoice', 'Can send invoices to customers')],
            },
        ),
        migrations.CreateModel(
            name='InvoiceLine',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=255)),
                ('quantity', models.DecimalField(decimal_places=3, default=Decimal('1.000'), max_digits=12)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=14)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('line_total', models.DecimalField(decimal_places=2, max_digits=14)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='billing.invoice')),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceEmailLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('to_email', models.EmailField(max_length=254)),
                ('success', models.BooleanField()),
                ('error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_logs', to='billing.invoice')),
            ],
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['customer', '-created_at'], name='billing_inv_custome_4b1fc0_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['status', 'due_date'], name='billing_inv_status_996e80_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['subscription_id', 'period_start', 'period_end'], name='billing_inv_subscri_e7c818_idx'),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.UniqueConstraint(condition=models.Q(('period_end__isnull', False), ('period_start__isnull', False), ('subscription_id__gt', ''), models.Q(('status', 'cancelled'), _negated=True)), fields=('subscription_id', 'period_start', 'period_end'), name='unique_subscription_period_invoice'),
        ),
    ]
