var embed = document.createElement('script')
embed.src = 'http://localhost:5000/embed.js'
embed.onload = function () { embed.remove() }
document.body.appendChild(embed)
