window.onloadTurnstileCallback = function () {
    console.log('Turnstile callback loaded');
    
    turnstile.render('#turnstile-widget', {
        sitekey: '0x4AAAAAABnxQRYqqyqYqnUZ', 
        theme: 'dark',
        size: 'normal',
        callback: function(token) {
            console.log('Turnstile verified:', token);
            localStorage.setItem('turnstileToken', token);
            
            const googleBtn = document.querySelector('.google-btn');
            if (googleBtn) {
                googleBtn.style.opacity = '1';
                googleBtn.style.pointerEvents = 'auto';
                googleBtn.style.background = 'rgba(26, 26, 26, 0.8)';
                googleBtn.style.borderColor = 'rgba(244, 108, 94, 0.3)';
            }
        },
        'error-callback': function(error) {
            console.log('Turnstile verification failed:', error);
            
            const googleBtn = document.querySelector('.google-btn');
            if (googleBtn) {
                googleBtn.style.opacity = '0.5';
                googleBtn.style.pointerEvents = 'none';
            }
        },
        'expired-callback': function() {
            console.log('Turnstile token expired');
            
            //disable the Google button again
            const googleBtn = document.querySelector('.google-btn');
            if (googleBtn) {
                googleBtn.style.opacity = '0.5';
                googleBtn.style.pointerEvents = 'none';
            }
        }
    });
};

//initially disable the Google button until Turnstile is verified
document.addEventListener('DOMContentLoaded', function() {
    const googleBtn = document.querySelector('.google-btn');
    if (googleBtn) {
        googleBtn.style.opacity = '0.5';
        googleBtn.style.pointerEvents = 'none';
        googleBtn.style.background = 'rgba(26, 26, 26, 0.4)';
        googleBtn.style.borderColor = 'rgba(244, 108, 94, 0.1)';
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const googleBtn = document.querySelector('.google-btn');
    if (googleBtn) {
        googleBtn.addEventListener('click', function (e) {
            const token = localStorage.getItem('turnstileToken');
            if (!token) {
                e.preventDefault();
                alert("Please complete the CAPTCHA.");
                return;
            }
            
            googleBtn.href = `https://n8nsync-server.onrender.com/login?captchaToken=${token}`;
        });
    }
});
