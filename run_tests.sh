#!/bin/bash

SEED=42
MAX_PLIES=300
OUTPUT_TXT="resultados_finais.txt"
OUTPUT_CSV="dados_analise.csv"

echo "ID,Confronto,White_Wins,Black_Wins,Draws,Avg_Moves" > $OUTPUT_CSV
echo "=== RELATÓRIO DE EXPERIMENTOS ANGULUS ===" > $OUTPUT_TXT
echo "Seed Fixa: $SEED" >> $OUTPUT_TXT

run_test() {
    local id=$1
    local desc=$2
    local cmd_args=$3

    echo "A executar $id: $desc..."
    
    # Correr o comando
    result=$(python main.py --seed $SEED --max-plies $MAX_PLIES --ai-vs-ai $cmd_args)
    
    echo -e "\n[$id] $desc" >> $OUTPUT_TXT
    echo "$result" >> $OUTPUT_TXT
    
    # Extração de dados compatível com Windows/Git Bash
    w=$(echo "$result" | python -c "import sys, re; res=sys.stdin.read(); m=re.search(r\"'white': (\d+)\", res); print(m.group(1)) if m else print(0)")
    b=$(echo "$result" | python -c "import sys, re; res=sys.stdin.read(); m=re.search(r\"'black': (\d+)\", res); print(m.group(1)) if m else print(0)")
    d=$(echo "$result" | python -c "import sys, re; res=sys.stdin.read(); m=re.search(r\"'draw': (\d+)\", res); print(m.group(1)) if m else print(0)")
    m=$(echo "$result" | python -c "import sys, re; res=sys.stdin.read(); m=re.search(r\"'avg_winner_moves_per_game': ([\d.]+)\", res); print(m.group(1)) if m else print(0)")
    
    echo "$id,$desc,$w,$b,$d,$m" >> $OUTPUT_CSV
}

# Lista de Testes - Atualizada para 30 rodadas onde Minimax 2 está presente
run_test "T1" "Random_vs_Random" "random random 100"
run_test "T2" "Minimax1_vs_Minimax1" "minimax 1 minimax 1 100"
run_test "T3" "Minimax2_vs_Minimax2" "minimax 2 minimax 2 30"
run_test "T4" "Minimax1_vs_Random" "minimax 1 random 100"
run_test "T5" "Minimax2_vs_Random" "minimax 2 random 30"
run_test "T6" "Minimax2_vs_Minimax1" "minimax 2 minimax 1 30"
run_test "T7" "MCTS_vs_Minimax2" "mcst 1 minimax 2 30"

echo "---------------------------------------"
echo " Concluído! Verifica 'dados_analise.csv'"
