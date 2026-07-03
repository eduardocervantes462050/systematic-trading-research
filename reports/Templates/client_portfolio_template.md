# Client Portfolio Report

**Client ID:** {{ client_id }}  
**Date:** {{ date }}  
**Total Portfolios:** {{ portfolios | length }}

---

{% for p in portfolios %}

## {{ p.name }}

### Holdings

| Symbol | Quantity | Avg Price |
|--------|----------|-----------|
{% for h in p.holdings %}
| {{ h.symbol }} | {{ "%.4f"|format(h.quantity) }} | {{ "%.2f"|format(h.avg_price) }} |
{% endfor %}

### Portfolio Concentration Metrics

- **HHI:** {{ p.metrics.hhi if p.metrics.hhi is not none else "N/A" }}
- **ENH:** {{ p.metrics.enh if p.metrics.enh is not none else "N/A" }}
- **Top 5 Concentration:** {{ p.metrics.top5 if p.metrics.top5 is not none else "N/A" }}
- **Biggest Position:** {{ p.metrics.big_single if p.metrics.big_single is not none else "N/A" }}

---

{% endfor %}