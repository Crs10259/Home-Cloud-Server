// Password-related functionality
document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const togglePasswordButtons = document.querySelectorAll('.btn[id^="togglePassword"]');
    
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.id.replace('toggle', '').toLowerCase();
            const passwordInput = document.getElementById(targetId) || 
                                  document.querySelector('input[type="password"][name="' + targetId + '"]') ||
                                  this.closest('.input-group').querySelector('input[type="password"]');
            
            if (!passwordInput) return;
            
            // Toggle the password visibility
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Toggle the eye icon
            const eyeIcon = this.querySelector('i');
            if (eyeIcon) {
                eyeIcon.classList.toggle('fa-eye');
                eyeIcon.classList.toggle('fa-eye-slash');
            }
        });
    });
    
    // Password validation - detect forms that need password matching
    const passwordForms = document.querySelectorAll('form:has(input[type="password"])');
    
    passwordForms.forEach(form => {
        const newPasswordInput = form.querySelector('input[name="password"], input[name="new_password"]');
        const confirmPasswordInput = form.querySelector('input[name="confirm_password"]');
        
        if (newPasswordInput && confirmPasswordInput) {
            // Setup validation
            function validatePassword() {
                if (newPasswordInput.value !== confirmPasswordInput.value) {
                    confirmPasswordInput.setCustomValidity("Passwords don't match");
                    confirmPasswordInput.classList.add('is-invalid');
                    
                    // Try to find feedback element
                    const feedback = form.querySelector('#password-feedback') || 
                                    confirmPasswordInput.parentNode.querySelector('.invalid-feedback');
                    
                    if (feedback) {
                        feedback.style.display = 'block';
                    }
                    
                    return false;
                } else {
                    confirmPasswordInput.setCustomValidity('');
                    confirmPasswordInput.classList.remove('is-invalid');
                    
                    // Try to find feedback element
                    const feedback = form.querySelector('#password-feedback') || 
                                    confirmPasswordInput.parentNode.querySelector('.invalid-feedback');
                    
                    if (feedback) {
                        feedback.style.display = 'none';
                    }
                    
                    return true;
                }
            }
            
            // Check on input change
            newPasswordInput.addEventListener('input', validatePassword);
            confirmPasswordInput.addEventListener('input', validatePassword);
            
            // Check before form submission
            form.addEventListener('submit', function(e) {
                if (newPasswordInput.value && !validatePassword()) {
                    e.preventDefault();
                }
            });
        }
    });
}); 