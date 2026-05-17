function getSettingsPage() {
    return `
    <div class="space-y-6">
        <div>
            <h2 class="text-2xl font-bold text-white">Pengaturan</h2>
            <p class="text-dark-400 text-sm mt-1">Kelola preferensi dan konfigurasi aplikasi</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2 space-y-6">
                <!-- Profile -->
                <div class="card p-5">
                    <h3 class="text-lg font-semibold text-white mb-4">Profil</h3>
                    <div class="flex items-center gap-4 mb-6">
                        <div class="w-16 h-16 bg-gradient-to-br from-emerald-400 to-cyan-500 rounded-full flex items-center justify-center">
                            <span class="text-2xl font-bold text-white">A</span>
                        </div>
                        <div>
                            <p class="text-lg font-medium text-white">Admin</p>
                            <p class="text-sm text-dark-400">admin@sahamid.com</p>
                            <p class="text-xs text-primary-400 mt-1"><i class="fas fa-crown mr-1"></i>Pro Member</p>
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Nama</label>
                            <input type="text" value="Admin" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        </div>
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Email</label>
                            <input type="email" value="admin@sahamid.com" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        </div>
                    </div>
                </div>

                <!-- Notifications -->
                <div class="card p-5">
                    <h3 class="text-lg font-semibold text-white mb-4">Notifikasi</h3>
                    <div class="space-y-4">
                        ${settingToggle('Email Notification', 'Terima sinyal dan alert via email', true)}
                        ${settingToggle('Telegram Bot', 'Kirim notifikasi ke Telegram', true)}
                        ${settingToggle('Push Notification', 'Notifikasi browser', false)}
                        ${settingToggle('Daily Summary', 'Ringkasan harian via email', true)}
                        ${settingToggle('Price Alert', 'Alert ketika target harga tercapai', true)}
                    </div>
                </div>

                <!-- Trading Preferences -->
                <div class="card p-5">
                    <h3 class="text-lg font-semibold text-white mb-4">Preferensi Trading</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Broker</label>
                            <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                                <option>Ajaib Sekuritas</option>
                                <option>Stockbit (Bibit)</option>
                                <option>Indo Premier (IPOT)</option>
                                <option>Mirae Asset</option>
                                <option>BCA Sekuritas</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Fee Buy (%)</label>
                            <input type="number" value="0.15" step="0.01" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        </div>
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Fee Sell (%)</label>
                            <input type="number" value="0.25" step="0.01" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        </div>
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Default Timeframe</label>
                            <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                                <option>Daily</option>
                                <option>Weekly</option>
                                <option>Monthly</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- API Configuration -->
                <div class="card p-5">
                    <h3 class="text-lg font-semibold text-white mb-4">API & Integrasi</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Telegram Bot Token</label>
                            <div class="flex gap-2">
                                <input type="password" value="xxxxxxxxxxxxxxx" class="flex-1 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                                <button class="px-3 py-2 bg-dark-700 text-dark-300 rounded-lg text-sm hover:bg-dark-600"><i class="fas fa-eye"></i></button>
                            </div>
                        </div>
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Telegram Chat ID</label>
                            <input type="text" value="123456789" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Sidebar -->
            <div class="space-y-4">
                <!-- Theme -->
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-white mb-3">Tampilan</h3>
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-dark-300">Dark Mode</span>
                            <div class="w-10 h-5 bg-primary-600 rounded-full relative cursor-pointer">
                                <div class="w-4 h-4 bg-white rounded-full absolute top-0.5 right-0.5"></div>
                            </div>
                        </div>
                        <div>
                            <label class="text-xs text-dark-400 mb-1 block">Warna Aksen</label>
                            <div class="flex gap-2">
                                <div class="w-6 h-6 rounded-full bg-blue-500 cursor-pointer ring-2 ring-white ring-offset-2 ring-offset-dark-900"></div>
                                <div class="w-6 h-6 rounded-full bg-emerald-500 cursor-pointer"></div>
                                <div class="w-6 h-6 rounded-full bg-purple-500 cursor-pointer"></div>
                                <div class="w-6 h-6 rounded-full bg-amber-500 cursor-pointer"></div>
                                <div class="w-6 h-6 rounded-full bg-rose-500 cursor-pointer"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Data Source -->
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-white mb-3">Sumber Data</h3>
                    <div class="space-y-2">
                        <div class="flex items-center justify-between p-2 bg-dark-800 rounded">
                            <span class="text-xs text-dark-300">Yahoo Finance</span>
                            <span class="text-xs text-success"><i class="fas fa-check-circle"></i> Aktif</span>
                        </div>
                        <div class="flex items-center justify-between p-2 bg-dark-800 rounded">
                            <span class="text-xs text-dark-300">IDX API</span>
                            <span class="text-xs text-success"><i class="fas fa-check-circle"></i> Aktif</span>
                        </div>
                        <div class="flex items-center justify-between p-2 bg-dark-800 rounded">
                            <span class="text-xs text-dark-300">GoAPI</span>
                            <span class="text-xs text-dark-500"><i class="fas fa-times-circle"></i> Nonaktif</span>
                        </div>
                    </div>
                </div>

                <!-- Account Actions -->
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-white mb-3">Akun</h3>
                    <div class="space-y-2">
                        <button class="w-full px-4 py-2 bg-dark-800 text-dark-300 rounded-lg text-sm hover:bg-dark-700 text-left"><i class="fas fa-download mr-2"></i>Export Data</button>
                        <button class="w-full px-4 py-2 bg-dark-800 text-dark-300 rounded-lg text-sm hover:bg-dark-700 text-left"><i class="fas fa-key mr-2"></i>Ganti Password</button>
                        <button class="w-full px-4 py-2 bg-danger/20 text-danger rounded-lg text-sm hover:bg-danger/30 text-left"><i class="fas fa-sign-out-alt mr-2"></i>Logout</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Save Button -->
        <div class="flex justify-end">
            <button class="px-6 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
                <i class="fas fa-save mr-2"></i>Simpan Pengaturan
            </button>
        </div>
    </div>`;
}

function settingToggle(title, desc, active) {
    return `
    <div class="flex items-center justify-between">
        <div>
            <p class="text-sm text-white">${title}</p>
            <p class="text-xs text-dark-400">${desc}</p>
        </div>
        <div class="w-10 h-5 ${active ? 'bg-primary-600' : 'bg-dark-600'} rounded-full relative cursor-pointer">
            <div class="w-4 h-4 bg-white rounded-full absolute top-0.5 ${active ? 'right-0.5' : 'left-0.5'}"></div>
        </div>
    </div>`;
}
