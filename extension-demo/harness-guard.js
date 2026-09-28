// index.html is the member-simulator test harness, not the product. Product UI is dashboard.html.
if (!new URLSearchParams(location.search).has('harness')) location.replace('dashboard.html');
