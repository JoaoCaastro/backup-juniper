#Importando bibliotecas necessárias
import scapy.all as scapy
import requests
import os
from time import strftime
from datetime import date

#Importa IP e Hostname do arquivo hosts.py
from hosts import ip, hostname

from netmiko import ConnectHandler


#Criando funçao para backup e geração dos logs
def gera_backup():

    #Definindo variáveis
    
    #Telegram Token Bot
    TOKEN = 'TOKEN_BOT'

    #ID do chat de mensagens
    chat_id = 'CHAT_ID'

    #Usuário e pass juniper device
    username = 'XXXXXXXXXX'
    password = 'XXXXXXXXXX'
    
    #Comando executado no device
    command = "show configuration | display set"

    #Path para arquivo de log
    arquivo = '/var/log/file.log'

    #Formatacao de data para log data e hora atual <Dia.Mês.Ano Hora:Minutos:Segundos>
    date_format = strftime('%d.%m.%Y %H:%M:%S')

    #Formatacao para criacao de diretório com a data atual <Dia-Mês-Ano>
    data = strftime('%d-%m-%Y')

    #Realiza a validacao do diretório, /mnt/backup/<data atual>
    is_exist = os.path.exists('/mnt/backup/' + data)

    #Se o diretório já existir
    if is_exist:

        #Gera Log de erro com data e hora do ocorrido
        log_file = open(arquivo, 'a')
        log_file.write("[" + date_format + "] >> Diretório Existente Falha! /" + data)
        log_file.write("\n")

	#Envia notificação via Telegram com o problema
        message = f"❌ Backup Failed\n Diretório de Backup já existente! \n *Revise o Script* \n Diretório: /" + data
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
        requests.get(url)

        exit()

    #Caso o diretório não exista
    elif not is_exist:

	#Cria o diretório com a data atual e segue script
        os.mkdir('/mnt/backup/' + data)

        #Laço de repetição conforme o número de itens da lista
        for i in range(len(ip)):

            #Realiza um teste de ping para o Host antes de continuar
            resposta = scapy.sr1(scapy.IP(dst=ip[i])/scapy.ICMP(), timeout=3)

    	    #Realiza validação do retorno do "PING" feito pelo sr1
            if resposta is not None:

                #Parametros para conexão ao Juniper device e comando executado
                junos_device = {'device_type': 'juniper_junos', 'host': ip[i], 'username': username, 'password': password}
                dev = ConnectHandler(**junos_device)
                command_output = dev.send_command(command)

                #Cria arquivo de backup com o nome do Host e insere a saída do comando
                f=open("/mnt/backup/" + data + '/'  + hostname[i], "w")
                f.write(command_output)
                f.closed
                dev.disconnect()

	           #Gera Log com data, nome do host e status do Backup realizado
                log_file = open(arquivo, 'a')
                log_file.write("[" + date_format + "] " + hostname[i] + " >> Backup OK")
                log_file.write("\n")

	            #Envia mensagem de Sucesso ou Falha do Bakcup para o Telegram
                message = f"✅ Backup Success\n Host: {hostname[i]}\n Data: {date_format}\n IP: {ip[i]}"
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
                requests.get(url)
                i += 1

            #Caso o Host não responda ao ping, falha o Backup do Host e continua a lista
            else:
                log_file = open(arquivo, 'a')
                log_file.write("[" + date_format + "] " + hostname[i] + " >> Host unreachable - Backup FAILED")
                log_file.write("\n")

                message = f"❌ Backup Failed\n Host: {hostname[i]}\n Data: {date_format}\n IP: {ip[i]}"
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
                requests.get(url)

                #Incrementa o contador da lista
                i += 1

    #Busca e rotaciona backups com +7 dias
    os.system('find /mnt/backup -mtime +7 -delete')

#Chama a função gera_backup()
gera_backup()
