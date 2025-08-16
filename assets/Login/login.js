document.addEventListener('DOMContentLoaded', () => {
    // Sélection des éléments
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('emailField');
    const passwordInput = document.getElementById('passwordField');
    const loginButton = document.querySelector('.login-button');
    const togglePassword = document.getElementById('togglePassword');

    // Identifiants valides
    const validCredentials = {
        email: 'admin@ccabank.com',
        password: 'admin123'
    };

    // Fonction pour vérifier si un email est valide
    const isValidEmail = (email) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    };

    // Fonction pour afficher un message
    const showMessage = (message, isError = true) => {
        console.log('Message:', message); // Pour le débogage
        
        // Supprime l'ancien message s'il existe
        const existingMessage = document.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isError ? 'error-message' : 'success-message'}`;
        messageDiv.style.color = isError ? '#ff3333' : '#4CAF50';
        messageDiv.style.fontSize = '14px';
        messageDiv.style.marginTop = '10px';
        messageDiv.style.textAlign = 'center';
        messageDiv.style.padding = '10px';
        messageDiv.textContent = message;

        loginButton.insertAdjacentElement('afterend', messageDiv);

        if (!isError) {
            messageDiv.style.backgroundColor = '#E8F5E9';
            messageDiv.style.border = '1px solid #4CAF50';
        } else {
            messageDiv.style.backgroundColor = '#FFEBEE';
            messageDiv.style.border = '1px solid #ff3333';
        }

        // Faire disparaître le message après 3 secondes
        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    };

    // Gestionnaire de soumission du formulaire
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        console.log('Formulaire soumis'); // Pour le débogage

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        console.log('Email saisi:', email); // Pour le débogage
        console.log('Mot de passe saisi:', password); // Pour le débogage

        // Validation des champs
        if (!email || !password) {
            showMessage('Veuillez remplir tous les champs', true);
            return;
        }

        // Validation du format de l'email
        if (!isValidEmail(email)) {
            showMessage('Veuillez entrer une adresse email valide', true);
            return;
        }

        // Validation du mot de passe
        if (password.length < 6) {
            showMessage('Le mot de passe doit contenir au moins 6 caractères', true);
            return;
        }

        // Désactive le bouton et montre le chargement
        loginButton.disabled = true;
        loginButton.textContent = 'Connexion en cours...';

        // Simulation de la vérification
        setTimeout(() => {
            console.log('Vérification des identifiants...'); // Pour le débogage
            console.log('Email attendu:', validCredentials.email);
            console.log('Mot de passe attendu:', validCredentials.password);

            if (email === validCredentials.email && password === validCredentials.password) {
                console.log('Connexion réussie!'); // Pour le débogage
                showMessage('Connexion réussie! Redirection...', false);
                
                // Stockage de l'état de connexion
                sessionStorage.setItem('isLoggedIn', 'true');
                sessionStorage.setItem('userEmail', email);

                // Redirection après un court délai
                setTimeout(() => {
                    window.location.href = '../index.html';
                }, 1500);
            } else {
                console.log('Échec de la connexion'); // Pour le débogage
                showMessage('Email ou mot de passe incorrect', true);
                loginButton.disabled = false;
                loginButton.textContent = 'Se connecter';
            }
        }, 1000);
    });

    // Gestion du toggle password
    togglePassword.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        this.textContent = type === 'password' ? 'visibility_off' : 'visibility';
    });

    // Gestion de la visibilité de l'icône œil
    passwordInput.addEventListener('input', function() {
        togglePassword.style.opacity = this.value.length > 0 ? '1' : '0';
        togglePassword.style.visibility = this.value.length > 0 ? 'visible' : 'hidden';
    });
});