"""
Dielectric Sensor Calibration Model
Capacitive Soil Moisture Sensor — Thermal Drift Compensation & Signal Filtering

Author: Efe Mert Çağdaş Padar
Institution: Çanakkale Onsekiz Mart Üniversitesi, Fizik Bölümü
Target: Agrinoms R&D Department, Çanakkale Teknopark
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d

np.random.seed(42)

# ── Zaman ekseni: 24 saat, 1 dakika çözünürlük ──
t = np.linspace(0, 24, 1440)

# ── Gerçek nem (ground truth) ──
theta_true = 0.28 + 0.01 * np.sin(2 * np.pi * t / 24 - np.pi)

# ── Topp denklemi (θ → ε) ──
def topp_forward(theta):
    return 3.8 + 34.2 * theta + 14.5 * theta**2

# ── Topp tersi (ε → θ) ──
def topp_inverse(eps):
    theta = -5.3e-2 + 2.92e-2*eps - 5.5e-4*eps**2 + 4.3e-6*eps**3
    return np.clip(theta, 0, 1)

eps_true = topp_forward(theta_true)

# ── Sıcaklık: 24 saatlik sinüs döngüsü (gece 10°C, gündüz 32°C) ──
T = 21 + 11 * np.sin(2 * np.pi * t / 24 - np.pi / 2)
T_ref = 25.0

# ── Termal sapma ──
delta_eps_thermal = -0.35 * (T - T_ref)

# ── Gaussian beyaz gürültü ──
noise = np.random.normal(0, 0.8, len(t))

# ── Ham sensör sinyali ──
eps_raw = eps_true + delta_eps_thermal + noise
theta_raw = topp_inverse(eps_raw)

# ── Adım 1: Termal kompanzasyon ──
eps_compensated = eps_raw - delta_eps_thermal
theta_compensated = topp_inverse(eps_compensated)

# ── Adım 2: Hareketli ortalama filtresi (30 dakika) ──
eps_filtered = uniform_filter1d(eps_compensated, size=30)
theta_filtered = topp_inverse(eps_filtered)

# ── Hata metrikleri ──
rmse_raw  = np.sqrt(np.mean((theta_raw - theta_true)**2)) * 100
rmse_comp = np.sqrt(np.mean((theta_compensated - theta_true)**2)) * 100
rmse_filt = np.sqrt(np.mean((theta_filtered - theta_true)**2)) * 100

print(f"Ham Veri RMSE        : {rmse_raw:.2f}%")
print(f"Kompanzasyon RMSE    : {rmse_comp:.2f}%")
print(f"Tam Filtreleme RMSE  : {rmse_filt:.2f}%")

# ════════════════════════════════════════
# GRAFİK 1 — Gürültü ve Sıcaklık Etkisi
# ════════════════════════════════════════
fig, axes = plt.subplots(3, 1, figsize=(11, 9), facecolor='#F8F9FA')
fig.suptitle('Grafik 1: Ham Sensör Verisinde Gürültü ve Sıcaklık Sapması',
             fontsize=13, fontweight='bold')

# Panel A — Sıcaklık
ax = axes[0]
ax.plot(t, T, color='#E74C3C', linewidth=2)
ax.axhline(T_ref, color='gray', linestyle='--', linewidth=1, label=f'Referans ({T_ref}°C)')
ax.fill_between(t, T, T_ref, where=(T > T_ref), alpha=0.15, color='#E74C3C')
ax.fill_between(t, T, T_ref, where=(T < T_ref), alpha=0.15, color='#3498DB')
ax.set_ylabel('Sıcaklık (°C)')
ax.set_title('(A) 24 Saatlik Sıcaklık Döngüsü', loc='left', fontsize=10)
ax.legend()
ax.grid(alpha=0.3)

# Panel B — Dielektrik
ax = axes[1]
ax.plot(t, eps_true, color='#2ECC71', linewidth=2.5, label='Gerçek ε')
ax.plot(t, eps_raw,  color='#E67E22', linewidth=0.8, alpha=0.7, label='Ham sensör ε')
ax.set_ylabel('Dielektrik Katsayısı (ε)')
ax.set_title('(B) Gerçek vs. Ham Dielektrik', loc='left', fontsize=10)
ax.legend()
ax.grid(alpha=0.3)

# Panel C — VWC
ax = axes[2]
ax.plot(t, theta_true * 100, color='#2ECC71', linewidth=2.5, label='Gerçek VWC')
ax.plot(t, theta_raw  * 100, color='#E67E22', linewidth=0.8, alpha=0.6, label='Ham VWC')
ax.set_ylabel('VWC (%)')
ax.set_xlabel('Zaman (saat)')
ax.set_title(f'(C) VWC Karşılaştırması — Ham RMSE: {rmse_raw:.1f}%', loc='left', fontsize=10)
ax.legend()
ax.grid(alpha=0.3)

for ax in axes:
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('grafik1_gurultu_sicaklik.png', dpi=150, bbox_inches='tight')
plt.show()

# ════════════════════════════════════════
# GRAFİK 2 — Filtreleme ve Yakınsama
# ════════════════════════════════════════
fig, axes = plt.subplots(3, 1, figsize=(11, 9), facecolor='#F8F9FA')
fig.suptitle('Grafik 2: Filtreleme Sonrası Gerçek Neme Yakınsama',
             fontsize=13, fontweight='bold')

# Panel A — Adım adım filtreleme
ax = axes[0]
ax.plot(t, theta_raw         * 100, color='#E67E22', linewidth=0.7, alpha=0.5, label='Ham')
ax.plot(t, theta_compensated * 100, color='#9B59B6', linewidth=1.2, alpha=0.8, label='Kompanzasyon')
ax.plot(t, theta_filtered    * 100, color='#2980B9', linewidth=2.2, label='Tam filtre')
ax.plot(t, theta_true        * 100, color='#27AE60', linewidth=2.5, linestyle='--', label='Gerçek')
ax.set_ylabel('VWC (%)')
ax.set_title('(A) Adım Adım Filtreleme', loc='left', fontsize=10)
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel B — Mutlak hata
error_raw  = np.abs(theta_raw      - theta_true) * 100
error_filt = np.abs(theta_filtered - theta_true) * 100
ax = axes[1]
ax.fill_between(t, error_raw,  alpha=0.3, color='#E74C3C', label=f'Ham (ort. {error_raw.mean():.1f}%)')
ax.fill_between(t, error_filt, alpha=0.5, color='#2980B9', label=f'Filtreli (ort. {error_filt.mean():.1f}%)')
ax.axhline(1.5, color='#27AE60', linestyle=':', linewidth=1.5, label='%1.5 hedef')
ax.set_ylabel('Mutlak Hata (%)')
ax.set_title('(B) Zaman İçinde Hata', loc='left', fontsize=10)
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel C — RMSE bar grafik
ax = axes[2]
kategoriler = ['Ham\nVeri', 'Sıcaklık\nKompanzasyonu', 'Tam\nFiltreleme']
degerler    = [rmse_raw, rmse_comp, rmse_filt]
renkler     = ['#E74C3C', '#E67E22', '#27AE60']
bars = ax.bar(kategoriler, degerler, color=renkler, width=0.45, edgecolor='white')
for bar, val in zip(bars, degerler):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.03,
            f'{val:.2f}%', ha='center', fontweight='bold', fontsize=11)
ax.axhline(1.5, color='#27AE60', linestyle='--', linewidth=1.5, label='Hedef: %1.5')
ax.set_ylabel('RMSE (%)')
ax.set_ylim(0, 6)
ax.set_title('(C) RMSE İyileşme Özeti', loc='left', fontsize=10)
ax.legend()
ax.grid(alpha=0.3, axis='y')

for ax in axes[:2]:
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3))

for ax in axes:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('grafik2_filtreleme_yakinsamasi.png', dpi=150, bbox_inches='tight')
plt.show()