# Bot Factory - Monetization & Growth Design

**Date:** 2026-02-10
**Status:** Approved for Implementation

---

## Executive Summary

Comprehensive plan to transform Bot Factory into a monetizable SaaS platform with hybrid pricing model, improved UX for conversion, and growth mechanisms (referral + affiliate programs).

**Target Metrics:**
- Time to first bot < 5 minutes
- Free→Paid conversion: 3-5%
- MRR $5k+ within 6 months
- 30% traffic from referrals
- Churn rate < 5%/month

---

## Section 1: UX Improvements

### 1.1 Smart Onboarding Wizard
- 5-step guided flow instead of blank state
- Template selection (Support, Sales, FAQ, Custom)
- Auto-validate Telegram token
- Preset personalities (Friendly, Professional, Casual)
- Test chat immediately after creation

### 1.2 Bot Template Library
| Template | Use Case | Preset Config |
|----------|----------|---------------|
| 🛒 E-commerce | Product catalog, orders, shipping | Pre-filled system instruction |
| 💼 B2B Lead Gen | Lead capture, qualification | Pre-filled |
| 📚 FAQ Bot | Knowledge base responses | RAG enabled by default |
| 🎫 Support | Issue resolution, escalation | Pre-filled |
| 🎰 Custom | Advanced users | Clean slate |

### 1.3 Progressive Disclosure
- **Basic mode**: Name, welcome message, AI model selection
- **Advanced mode**: Temperature, system instruction, thinking budget
- Toggle: "Show advanced settings"

### 1.4 Visual Progress Indicators
```tsx
Message usage: 847 / 1,000 (84%)
███████████████░░░░
Renew: 5 days
```

---

## Section 2: Hybrid Monetization Model

### 2.1 Pricing Structure

| Plan | Price/Mo | Bots | Messages | Storage | Overage Rate |
|------|----------|------|----------|---------|--------------|
| Free | $0 | 1 | 500/mo | 5 MB | $0.002/msg |
| Starter | $19 | 3 | 5,000/mo | 100 MB | $0.0015/msg |
| Pro | $49 | 10 | 25,000/mo | 500 MB | $0.001/msg |
| Enterprise | $199 | ∞ | 150,000/mo | 5 GB | $0.0005/msg |

### 2.2 Data Models

```python
# billing/models.py
class Subscription(models.Model):
    tenant = OneToOneField(Tenant)
    plan = CharField(choices=PLAN_CHOICES)
    status = CharField(active/paused/canceled/overdue)
    current_period_start = DateTimeField()
    current_period_end = DateTimeField()
    base_messages_limit = IntegerField()
    overage_messages_used = IntegerField(default=0)
    overage_cost_cents = IntegerField(default=0)
    payment_method = CharField(stripe/coinbase/crypto)
    stripe_customer_id = CharField(blank=True)
    auto_renew = BooleanField(default=True)

class UsageRecord(models.Model):
    tenant = ForeignKey(Tenant)
    bot = ForeignKey(Bot)
    date = DateField()
    messages_count = IntegerField()
    tokens_used = IntegerField()
    cost_cents = IntegerField()
    is_overage = BooleanField(default=False)

class Invoice(models.Model):
    tenant = ForeignKey(Tenant)
    amount_cents = IntegerField()
    currency = CharField(default='USD')
    status = CharField(draft/pending/paid/failed)
    due_date = DateTimeField()
    paid_date = DateTimeField(null=True)
    pdf_url = URLField(blank=True)
```

### 2.3 Payment Providers
- **Stripe** - Cards, Apple Pay, Google Pay (primary)
- **Coinbase Commerce** - Crypto (BTC, ETH, USDC)
- **YooKassa** - Russia (if needed)
- **Paddle/Lemon Squeezy** - Merchant of Record (taxes)

### 2.4 Triggers
- 80% limit usage → notification
- Limit exhausted → bot paused
- 1 day before renewal → reminder
- 3 days non-payment → downgrade to Free

---

## Section 3: Growth & Marketing

### 3.1 Referral Program

```python
class ReferralProgram(models.Model):
    tenant = OneToOneField(Tenant)
    referral_code = CharField(unique=True)  # "BOTFACTORY-JOHN"
    total_referrals = IntegerField(default=0)
    successful_referrals = IntegerField(default=0)
    credits_earned_cents = IntegerField(default=0)

# Rewards
REFERRER_REWARD = $20 per successful referral
REFERRAL_WELCOME_BONUS = $10 for new user
```

### 3.2 Public Template Marketplace
- SEO-optimized pages (`/templates/ecommerce-shop-bot`)
- Live demo for each template
- Reviews and ratings
- "Use this template" → registration flow

### 3.3 Affiliate Program

```python
class Affiliate(models.Model):
    user = ForeignKey(User)
    affiliate_id = CharField(unique=True)
    tier = CharField(bronze/silver/gold)
    commission_percent = IntegerField(default=20)
    total_earnings_cents = IntegerField(default=0)
    payout_method = CharField(stripe_paypal/crypto)

class AffiliateClick(models.Model):
    affiliate = ForeignKey(Affiliate)
    landing_page = URLField()
    converted = BooleanField(default=False)
```

### 3.4 Sunk Costs for Retention
- Progress bar during bot creation (80% ready!)
- Checkmarks for completed steps
- The more invested → harder to leave

---

## Section 4: Integrations

### 4.1 White-Label
```python
class WhiteLabelSettings(models.Model):
    tenant = OneToOneField(Tenant)
    custom_domain = URLField()
    custom_logo = URLField()
    custom_colors = JSONField()
    remove_branding = BooleanField(default=False)
```

### 4.2 API for Developers
- REST API endpoints (partial implementation exists)
- Webhooks for events (`bot.message_received`, etc.)

### 4.3 Multi-Language
```python
class BotLocale(models.Model):
    bot = ForeignKey(Bot, related_name='locales')
    language = CharField()
    welcome_message = TextField()
    help_message = TextField()
    system_instruction = TextField()
```

### 4.4 Funnel Analytics
```python
class FunnelAnalytics(models.Model):
    bot = ForeignKey(Bot)
    new_users = IntegerField()
    first_message = IntegerField()
    conversation_start = IntegerField()
    goal_completion = IntegerField()
```

---

## Section 5: Implementation Roadmap

### Phase 1 - Critical (2-3 weeks)
1. Fix existing bugs
2. Stripe integration (basic)
3. Plan selection page with checkout
4. Hard limits on Free tier
5. Email notifications for limits

### Phase 2 - Important (3-4 weeks)
6. Onboarding wizard
7. 3-5 bot templates
8. Referral program (basic)
9. Billing history page
10. Usage dashboard

### Phase 3 - Enhancements (4-6 weeks)
11. Affiliate program
12. Public template marketplace
13. White-label for Enterprise
14. Extended analytics
15. Webhooks API

### YAGNI - Do NOT Build Yet
- Mobile app (PWA sufficient)
- Custom AI models
- Voice/video in bots
- Multi-language UI
- Third-party integrations marketplace

---

## Architecture Changes

```
backend/apps/
├── billing/           # NEW: invoices, payments, plans
├── referrals/         # NEW: referral program
├── templates/         # NEW: bot templates
├── affiliate/         # NEW: affiliate program
└── (existing apps...)
```

---

## Success Metrics

| Category | Key Metrics |
|----------|-------------|
| **UX** | Time to first bot < 5 min, completion rate > 70% |
| **Monetization** | Conversion Free→Paid 3-5%, MRR $5k+ in 6 mo |
| **Growth** | 30% traffic from referrals, 15% from SEO |
| **Retention** | Churn < 5%/mo, D30 retention > 40% |
