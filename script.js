// Configuration
const CONFIG = {
    ELITE_THRESHOLD: 600,
    CHESS_COM_API: 'https://api.chess.com/pub/player',
    LICHESS_API: 'https://lichess.org/api/user',
};

// DOM Elements
const platformSelect = document.getElementById('platform');
const usernameInput = document.getElementById('username');
const ratingInput = document.getElementById('rating');
const screenshotInput = document.getElementById('screenshot');
const verifyBtn = document.getElementById('verifyBtn');
const verifyMessage = document.getElementById('verifyMessage');
const rulesAccept = document.getElementById('rulesAccept');

// Event Listeners
verifyBtn.addEventListener('click', handleVerification);

// Main Verification Function
async function handleVerification() {
    // Reset message
    verifyMessage.className = 'verify-message';
    verifyMessage.textContent = '';

    // Validation
    const platform = platformSelect.value;
    const username = usernameInput.value.trim();
    const rating = ratingInput.value.trim();
    const screenshot = screenshotInput.files[0];
    const rulesAccepted = rulesAccept.checked;

    // Check if rules are accepted
    if (!rulesAccepted) {
        showMessage('يجب قبول القوانين والشروط أولاً', 'error');
        return;
    }

    // Check required fields
    if (!platform) {
        showMessage('اختر المنصة من فضلك (chess.com أو Lichess)', 'error');
        return;
    }

    if (!username) {
        showMessage('أدخل اسم المستخدم من فضلك', 'error');
        return;
    }

    // Show pending message
    showMessage('⏳ جاري التحقق من البيانات...', 'pending');
    verifyBtn.disabled = true;
    verifyBtn.textContent = 'جاري التحقق...';

    try {
        let verificationResult = null;

        // Try API verification first
        if (platform === 'chess.com') {
            verificationResult = await verifyChessDotCom(username);
        } else if (platform === 'lichess') {
            verificationResult = await verifyLichess(username);
        }

        // If API verification failed, check manual rating
        if (!verificationResult && rating) {
            verificationResult = verifyManualRating(parseInt(rating));
        }

        // If still no verification and screenshot exists, mark as pending admin review
        if (!verificationResult && screenshot) {
            showMessage('📸 تم رفع الصورة بنجاح! سيتم التحقق من قبل Admin قريباً. شكراً لصبرك!', 'pending');
            logVerificationAttempt({
                username,
                platform,
                method: 'screenshot',
                timestamp: new Date().toISOString(),
                status: 'pending_admin_review'
            });
            return;
        }

        // Process verification result
        if (verificationResult) {
            const category = verificationResult.rating >= CONFIG.ELITE_THRESHOLD ? 'Elite' : 'Beginners';
            const ratingDisplay = verificationResult.rating || ratingInput.value;

            showMessage(
                `✅ تم التحقق بنجاح!\nالريتينج: ${ratingDisplay}\nالفئة: ${category}\nسيتم توجيهك قريباً...`,
                'success'
            );

            // Log successful verification
            logVerificationAttempt({
                username,
                platform,
                rating: ratingDisplay,
                category,
                method: 'api_or_manual',
                timestamp: new Date().toISOString(),
                status: 'verified'
            });

            // Simulate redirect after delay
            setTimeout(() => {
                redirectToCategory(category);
            }, 2000);
        } else {
            showMessage(
                '❌ فشل التحقق. تأكد من:\n• اسم المستخدم صحيح\n• أدخل الريتينج يدوياً أو\n• ارفع صورة من حسابك',
                'error'
            );
        }
    } catch (error) {
        console.error('Verification error:', error);
        showMessage(
            '⚠️ حدث خطأ في التحقق. جرب لاحقاً أو ارفع صورة من حسابك',
            'error'
        );
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'تحقق من الريتينج';
    }
}

// Verify Chess.com
async function verifyChessDotCom(username) {
    try {
        const response = await fetch(`${CONFIG.CHESS_COM_API}/${username}`);
        if (!response.ok) throw new Error('User not found');

        const data = await response.json();
        const rating = data.stats?.blitz?.last?.rating || 
                       data.stats?.rapid?.last?.rating || 
                       data.stats?.classical?.last?.rating || 
                       null;

        if (!rating) {
            throw new Error('No rating found');
        }

        return { username, rating, platform: 'chess.com', verified: true };
    } catch (error) {
        console.warn('Chess.com verification failed:', error);
        return null;
    }
}

// Verify Lichess
async function verifyLichess(username) {
    try {
        const response = await fetch(`${CONFIG.LICHESS_API}/${username}`);
        if (!response.ok) throw new Error('User not found');

        const data = await response.json();
        const rating = data.perfs?.blitz?.rating || 
                       data.perfs?.rapid?.rating || 
                       data.perfs?.classical?.rating || 
                       null;

        if (!rating) {
            throw new Error('No rating found');
        }

        return { username, rating, platform: 'lichess', verified: true };
    } catch (error) {
        console.warn('Lichess verification failed:', error);
        return null;
    }
}

// Manual Rating Verification
function verifyManualRating(rating) {
    if (!rating || rating < 0 || rating > 3000) {
        return null;
    }
    return { rating, verified: true, method: 'manual' };
}

// Show Message
function showMessage(text, type) {
    verifyMessage.className = `verify-message ${type}`;
    verifyMessage.textContent = text;
    verifyMessage.style.display = 'block';
}

// Log Verification Attempt
function logVerificationAttempt(data) {
    const logs = JSON.parse(localStorage.getItem('verificationLogs') || '[]');
    logs.push(data);
    localStorage.setItem('verificationLogs', JSON.stringify(logs));
    console.log('Verification logged:', data);
}

// Redirect to Category
function redirectToCategory(category) {
    if (category === 'Elite') {
        // Replace with actual WhatsApp or group link
        alert('🎉 مرحباً بك في فئة النخبة!\nسيتم نقلك إلى جروب النخب��');
        // window.location.href = 'https://chat.whatsapp.com/elite-group-link';
    } else {
        // Replace with actual WhatsApp or group link
        alert('🎉 مرحباً بك في فئة المبتدئين!\nسيتم نقلك إلى جروب المبتدئين');
        // window.location.href = 'https://chat.whatsapp.com/beginners-group-link';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Arise Chess Platform Loaded ✓');
    console.log('Elite Threshold:', CONFIG.ELITE_THRESHOLD);

    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';

    // Disable verify button until rules are accepted
    updateVerifyButtonState();
    rulesAccept.addEventListener('change', updateVerifyButtonState);
});

function updateVerifyButtonState() {
    if (rulesAccept.checked) {
        verifyBtn.style.opacity = '1';
        verifyBtn.style.cursor = 'pointer';
    } else {
        verifyBtn.style.opacity = '0.6';
        verifyBtn.style.cursor = 'not-allowed';
    }
}

// Debug: Log all verification attempts to console
window.getVerificationLogs = () => {
    const logs = JSON.parse(localStorage.getItem('verificationLogs') || '[]');
    console.table(logs);
    return logs;
};

// Add real-time character counter for username
usernameInput.addEventListener('input', (e) => {
    const length = e.target.value.length;
    if (length > 0) {
        e.target.style.borderColor = length > 2 ? '#10b981' : '#fbbf24';
    }
});

// Add visual feedback for rating input
ratingInput.addEventListener('input', (e) => {
    const rating = parseInt(e.target.value) || 0;
    if (rating >= CONFIG.ELITE_THRESHOLD) {
        e.target.style.borderColor = '#fbbf24';
    } else if (rating > 0) {
        e.target.style.borderColor = '#1e3a8a';
    }
});