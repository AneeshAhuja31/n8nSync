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
}
document.addEventListener('DOMContentLoaded',async()=>{
    await checkexistingAuth();
})

