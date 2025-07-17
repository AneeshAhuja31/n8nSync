async function checkexistingAuth() {
    try{
        const response = await fetch("https://n8nsync-server.onrender.com/auth/validate",{
            method:"GET",
            credentials:"include" //include cookies
        })
        if(response.ok){
            const data = await response.json();
            if(data.valid){
                window.location.href = 'https://n8nsync.aneeshahuja.tech/chat.html'
                return;
            }
        }
    }
    catch (error){
        console.error('Auth validation error: ',error);
    }
    localStorage.clear();
    document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.aneeshahuja.tech;';
    document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    // Force a complete page reload to login page without cache
    window.location.replace('https://n8nsync.aneeshahuja.tech/login.html');
}
document.addEventListener('DOMContentLoaded',async()=>{
    await checkexistingAuth();
})

