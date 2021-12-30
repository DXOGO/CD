## Trabalho 4 Computação Distribuída 2020/2021

O objetivo deste trabalho é o desenvolvimento de um sistema de distribuição de carga HTTP (load
balancer).

Neste guião vamos considerar as seguintes políticas para escolher qual o servidor de
back-end:

- **N to one**: todo o tráfego é enviado para o primeiro servidor (desenvolvido apenas
  para o guião, não é usado na prática)
- **Round Robin**: uma das políticas mais simples. Cada pedido é enviado para o
  próximo servidor na lista. Quando o último servidor é usado, volta ao primeiro.
- **Least Connections**: é escolhido como próximo servidor aquele que tem menos
  ligações ativas no momento.
- Least Response Time: é escolhido como próximo servidor aquele que em média leva
  menos tempo a servir clientes.



# Autors:

Diogo Cruz: [DXOGO](https://github.com/DXOGO)   
Nuno Fahla: [broth2](https://github.com/broth2)