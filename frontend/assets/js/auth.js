async function validateAuth() {
    try{
        const response = await fetch("https://n8nsync-server.onrender.com/auth/validate/",{
            method:"GET",
            credentials:"include" //include cookies
        })

        if(response.ok){
            const data = await response.json();
            if(data.valid){
                localStorage.setItem('userName',data.user.name);
                localStorage.setItem('userEmail',data.user.email);
                return true;
            }
        }
        window.location.href = 'https://n8nsync.aneeshahuja.tech/login.html';
        return false;
    }
    catch (error){
        console.error('Auth validation error: ',error);
        window.location.href = 'https://n8nsync.aneeshahuja.tech/login.html';
        return false;
    }
}

async function logout() {
    try{
        await fetch('https://n8nsync-server.onrender.com/auth/logout',{
            method:'POST',
            credentials:'include',
            body:JSON.stringify({
                "email":localStorage.getItem("userEmail")
            })
        });
    } catch(error){
        console.error('Logout error: ',error);
    }
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('n8nApiKey');  
    localStorage.removeItem('geminiApiKey');
    localStorage.removeItem('n8nUri');

    window.location.href = 'https://n8nsync.aneeshahuja.tech/login.html';
}

async function clearCredentials() {
    localStorage.removeItem('n8nApiKey');  
    localStorage.removeItem('geminiApiKey');
    localStorage.removeItem('n8nUri');
    showApiKeyOverlay();
}

document.addEventListener('DOMContentLoaded',async()=>{
    checkApiKeys();
    const storedName = localStorage.getItem('userName');
    const storedEmail = localStorage.getItem('userEmail');
    const clearCredentialsBtn = document.getElementById("clearCredentials");
    const logoutBtn = document.getElementById('logoutBtn');
    const apiKeyForm = document.getElementById('apiKeyForm');
    
    if (storedName){
        const welcomeElement = document.getElementById('welcome');
        if (welcomeElement) {
            welcomeElement.innerText = `Welcome ${storedName}.`;
        }
    }
    await validateAuth();

    if(clearCredentialsBtn){
        clearCredentialsBtn.addEventListener("click",clearCredentials)
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const loader = document.getElementById("loader");
            const saveBtn = document.getElementById("saveBtn");
            loader.style.display = "block";
            saveBtn.disabled = true;
            const n8nUri = document.getElementById("n8nUri").value.trim();
            const n8nApiKey = document.getElementById('n8nApiKey').value.trim();
            const geminiApiKey = document.getElementById('geminiApiKey').value.trim();
            
            if (n8nApiKey && geminiApiKey) {
                
                const n8nValidationResponse = await fetch("https://n8nsync-server.onrender.com/validate-n8n-api-key", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body:JSON.stringify({
                            "n8nUrl":n8nUri,
                            "n8nApiKey":n8nApiKey
                        })
                    });
                if (n8nValidationResponse.ok){
                    n8nValidationData = await n8nValidationResponse.json();
                    if(!n8nValidationData.success){
                        loader.style.display = "none";
                        saveBtn.disabled = false;
                        if(n8nValidationData.message === "unauthorized"){
                            alert("❌Invalid n8n API Key or n8n instance not active");
                            return;
                        }
                        else if(n8nValidationData.message === "Connection Issue"){
                            alert("❌n8n Instance Offline/Problem connecting with your n8n cloud");
                            return;
                        }
                    }
                }
                const geminiValidationResponse = await fetch("https://n8nsync-server.onrender.com/validate-gemini-api-key", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body:JSON.stringify({
                            "geminiApiKey":geminiApiKey
                        })
                    });
                
                if (geminiValidationResponse.ok){
                    geminiValidationData = await geminiValidationResponse.json();
                    if(!geminiValidationData.success){
                        loader.style.display = "none";
                        saveBtn.disabled = false;
                        if(geminiValidationData.message === "Invalid or unauthorized API key"){
                            alert("❌Invalid or unauthorized API key");
                            return;
                        }
                        else if(geminiValidationData.message === "Quota exceeded or rate limited"){
                            alert("❌Gemini API Quota exceeded or rate limited");
                            return;
                        }
                        else if(geminiValidationData.message === "Connection Issue"){
                            alert("❌Gemini Connection Issue, please try again later!");
                            return;
                        }
                    }
                }
                loader.style.display = "none";
                saveBtn.disabled = false;
                saveApiKeys(n8nUri, n8nApiKey, geminiApiKey);
            }
        });
    }
    
})



function checkApiKeys() {
    const n8nApiKey = localStorage.getItem('n8nApiKey');
    const geminiApiKey = localStorage.getItem('geminiApiKey');
    const n8nUri = localStorage.getItem('n8nUri');
    
    if (!n8nApiKey || !geminiApiKey || !n8nUri) {
        showApiKeyOverlay();
        return false;
    }
    return true;
}

function saveApiKeys(n8nUri, n8nApiKey, geminiApiKey) {
    localStorage.setItem('n8nUri', n8nUri);
    localStorage.setItem('n8nApiKey', n8nApiKey);
    localStorage.setItem('geminiApiKey', geminiApiKey);
    
    hideApiKeyOverlay();
}

function showApiKeyOverlay() {
    localStorage.removeItem('n8nApiKey');
    localStorage.removeItem('geminiApiKey');
    localStorage.removeItem('n8nUri');
    
    const overlay = document.getElementById('apiKeyOverlay');
    const container = document.querySelector('.container');
    
    overlay.style.display = 'flex';
    container.classList.add('blurred');
}

function hideApiKeyOverlay() {
    const overlay = document.getElementById('apiKeyOverlay');
    const container = document.querySelector('.container');
    
    overlay.style.display = 'none';
    container.classList.remove('blurred');
}