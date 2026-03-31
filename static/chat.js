let currentChat = null


function handleKey(e){
    if(e.key === "Enter"){
        sendMessage()
    }
}


async function createChat(){

    let res = await fetch("/create_chat")

    let data = await res.json()

    currentChat = data.chat_id

    document.getElementById("messages").innerHTML=""

    loadChats()
}


async function loadChats(){

    let res = await fetch("/get_chats")
    let chats = await res.json()

    let list = document.getElementById("chat-list")

    list.innerHTML=""

    chats.forEach(chat=>{

        let div = document.createElement("div")

        div.className = "chat-item"

        div.innerHTML = `
        <span onclick="openChat(${chat.id})">${chat.title}</span>
        <button class="delete-btn" onclick="deleteChat(${chat.id})">✕</button>
        `

        list.appendChild(div)

    })

}
async function openChat(id){

    currentChat = id

    let res = await fetch("/get_messages/"+id)

    let msgs = await res.json()

    let box = document.getElementById("messages")
    box.innerHTML=""

    msgs.forEach(m=>{
        appendMessage(m.role, m.content)
    })

}
async function sendMessage(){

    let input = document.getElementById("message-input")
    let text = input.value

    if(!text) return

    input.value=""

    // Show user message (right side)
    appendMessage("user", text)

    // If no chat exists → create one
    if(currentChat == null){

        let res = await fetch("/create_chat")
        let data = await res.json()

        currentChat = data.chat_id
        loadChats()
    }

    // Show typing animation
    showTypingIndicator()

    let res = await fetch("/chat",{

        method:"POST",

        headers:{
        "Content-Type":"application/json"
        },

        body:JSON.stringify({
        message:text,
        chat_id:currentChat
        })

    })

    let data = await res.json()

    // Remove typing animation
    hideTypingIndicator()

    // Show AI message (left side)
    appendMessage("assistant", data.reply)
}

async function deleteChat(id){

    await fetch("/delete_chat/"+id)

    loadChats()

    document.getElementById("messages").innerHTML=""

}


loadChats()