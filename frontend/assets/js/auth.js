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
        window.location.href = 'http://localhost:3000/login';
        return false;
    }
    catch (error){
        console.error('Auth validation error: ',error);
        window.location.href = 'http://localhost:3000/login';
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
    localStorage.removeItem('n8nInstanceType')
    window.location.href = 'http://localhost:3000/login';
}

document.addEventListener('DOMContentLoaded',async()=>{
    checkApiKeys();
    const storedName = localStorage.getItem('userName');
    const storedEmail = localStorage.getItem('userEmail');
    const logoutBtn = document.getElementById('logoutBtn');
    const apiKeyForm = document.getElementById('apiKeyForm');
    const instanceTypeSelect = document.getElementById("n8nInstanceType");
    const cloudUriInput = document.getElementById("n8nCloudUri");
    
    if (storedName){
        const welcomeElement = document.getElementById('welcome');
        if (welcomeElement) {
            welcomeElement.innerText = `Welcome ${storedName}.`;
        }
    }
    await validateAuth();

    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    if(instanceTypeSelect){
        instanceTypeSelect.addEventListener("change",function(){
            const localhostMessage = document.getElementById("localhostMessage");
            if (this.value === "cloud"){
                cloudUriInput.style.display = "block";
                cloudUriInput.required = true;
                localhostMessage.style.display = "none";
            } 
            else {
                cloudUriInput.style.display = 'none';
                cloudUriInput.required = false;
                cloudUriInput.value = ''; 
                if (this.value === "localhost" && localhostMessage) {
                    localhostMessage.style.display = "block"; // Show localhost message
                }
            }
        });
    }

    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const loader = document.getElementById("loader");
            const saveBtn = document.getElementById("saveBtn");
            loader.style.display = "block";
            saveBtn.disabled = true;
            const instanceType = document.getElementById("n8nInstanceType").value;
            const n8nCloudUri = document.getElementById("n8nCloudUri").value.trim();
            const n8nApiKey = document.getElementById('n8nApiKey').value.trim();
            const geminiApiKey = document.getElementById('geminiApiKey').value.trim();
            let n8nURI = "";
            if (instanceType && n8nApiKey && geminiApiKey) {
                if (instanceType === 'cloud' && !n8nCloudUri) {
                    alert('Please enter the n8n Cloud URI');
                    return;
                }
                if(instanceType ==="cloud"){
                    n8nURI = n8nCloudUri;
                }
                else{
                    n8nURI = "http://localhost:5678";
                }
                const n8nValidationResponse = await fetch("https://n8nsync-server.onrender.com/validate-n8n-api-key", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body:JSON.stringify({
                            "n8nUrl":n8nURI,
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
                        else if(n8nValidationData.message === "Connection Issue" && n8nURI === "http://localhost:5678"){
                            alert("❌n8n Instance Offline, run n8n locally on terminal!");
                            return;
                        }
                        else if(n8nValidationData.message === "Connection Issue" && n8nURI === n8nCloudUri){
                            alert("❌Problem connecting with your n8n cloud, please try again later!");
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
                saveApiKeys(instanceType, n8nCloudUri, n8nApiKey, geminiApiKey);
            }
        });
    }
    
})



function checkApiKeys() {
    const n8nApiKey = localStorage.getItem('n8nApiKey');
    const geminiApiKey = localStorage.getItem('geminiApiKey');
    const n8nInstanceType = localStorage.getItem('n8nInstanceType');
    
    if (!n8nApiKey || !geminiApiKey || !n8nInstanceType) {
        showApiKeyOverlay();
        return false;
    }
    return true;
}

function saveApiKeys(instanceType, cloudUri, n8nApiKey, geminiApiKey) {
    localStorage.setItem('n8nInstanceType', instanceType);
    localStorage.setItem('n8nApiKey', n8nApiKey);
    localStorage.setItem('geminiApiKey', geminiApiKey);
    
    if (instanceType === 'cloud') {
        localStorage.setItem('n8nCloudUri', cloudUri);
    } else {
        localStorage.removeItem('n8nCloudUri');
    }
    
    hideApiKeyOverlay();
}

function showApiKeyOverlay() {
    localStorage.removeItem('n8nApiKey');
    localStorage.removeItem('geminiApiKey');
    localStorage.removeItem('n8nInstanceType');
    localStorage.removeItem('n8nCloudUri');
    
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