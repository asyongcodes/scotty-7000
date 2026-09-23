import streamlit as st
import random
from collections import Counter

# Set up page config for mobile screens
st.set_page_config(page_title="Scatter Slots Sim", layout="centered")

st.title("⚡ Gates of Python: Bonus Edition")
st.write("Match 8+ symbols. 4+ Scatter symbols (⚡) trigger 15 Free Spins with growing multipliers!")

# Initialize the game's persistent state data
if "balance" not in st.session_state:
    st.session_state.balance = 5000
if "last_win" not in st.session_state:
    st.session_state.last_win = 0
if "active_multiplier" not in st.session_state:
    st.session_state.active_multiplier = 1
if "grid" not in st.session_state:
    st.session_state.grid = [["💎" for _ in range(6)] for _ in range(5)]

# --- BONUS ROUND STATES ---
if "free_spins_left" not in st.session_state:
    st.session_state.free_spins_left = 0
if "is_in_bonus" not in st.session_state:
    st.session_state.is_in_bonus = False
if "global_bonus_multiplier" not in st.session_state:
    st.session_state.global_bonus_multiplier = 1
if "total_bonus_win" not in st.session_state:
    st.session_state.total_bonus_win = 0
if "current_bet" not in st.session_state:
    st.session_state.current_bet = 20

# Define game symbols, payouts, and weights
SYMBOLS_INFO = {
    "👑": {"payout": 50, "weight": 5},
    "💎": {"payout": 25, "weight": 10},
    "🍉": {"payout": 15, "weight": 15},
    "🍇": {"payout": 10, "weight": 25},
    "🍏": {"payout": 5,  "weight": 35}
}

SCATTER_BONUS_SYMBOL = "⚡"
MULTIPLIER_ORB_SYMBOL = "⭐"

# Core game mechanics function
def spin_engine(bet_amount):
    # Only deduct credits if we are playing a normal spin
    if not st.session_state.is_in_bonus:
        st.session_state.balance -= bet_amount
        st.session_state.current_bet = bet_amount
    else:
        st.session_state.free_spins_left -= 1
        # In free spins, use the bet size that triggered the bonus
        bet_amount = st.session_state.current_bet

    symbols_list = list(SYMBOLS_INFO.keys())
    weights_list = [SYMBOLS_INFO[s]["weight"] for s in symbols_list]
    
    # 1. Generate randomized 6x5 matrix
    new_grid = []
    all_flat_symbols = []
    multiplier_values_found = []
    
    # Slightly increase multiplier orb rates inside the bonus round for maximum fun
    orb_chance = 0.09 if st.session_state.is_in_bonus else 0.05
    
    for row_idx in range(5):
        row_symbols = random.choices(symbols_list, weights=weights_list, k=6)
        for col_idx in range(6):
            rand_roll = random.random()
            
            if rand_roll < 0.04:  # 4% chance for scatter
                row_symbols[col_idx] = SCATTER_BONUS_SYMBOL
            elif rand_roll < (0.04 + orb_chance):  # Orb chance
                row_symbols[col_idx] = MULTIPLIER_ORB_SYMBOL
                orb_value = random.choice([2, 5, 10, 25, 50])
                multiplier_values_found.append(orb_value)
                
        new_grid.append(row_symbols)
        all_flat_symbols.extend(row_symbols)
        
    st.session_state.grid = new_grid
    
    # 2. Parse wins using a Counter
    symbol_counts = Counter(all_flat_symbols)
    base_spin_win = 0
    win_breakdown_messages = []
    
    for symbol, count in symbol_counts.items():
        if symbol in SYMBOLS_INFO and count >= 8:
            base_payout = SYMBOLS_INFO[symbol]["payout"]
            calculated_win = base_payout * (count - 7) * (bet_amount / 20)
            base_spin_win += int(calculated_win)
            win_breakdown_messages.append(f"{symbol} x{count} matched!")
            
        elif symbol == SCATTER_BONUS_SYMBOL and count >= 4:
            # Hit 4 scatters! Trigger or re-trigger free spins
            bonus_win = bet_amount * 5  # Instant trigger prize
            base_spin_win += int(bonus_win)
            
            if st.session_state.is_in_bonus:
                st.session_state.free_spins_left += 5
                win_breakdown_messages.append(f"✨ SCATTER RE-TRIGGER! +5 Free Spins!")
            else:
                st.session_state.is_in_bonus = True
                st.session_state.free_spins_left = 15
                st.session_state.global_bonus_multiplier = 1
                st.session_state.total_bonus_win = 0
                win_breakdown_messages.append(f"✨ BONUS ROUND TRIGGERED! 15 FREE SPINS ACTIVATED!")

    # 3. Handle Multiplier Logic (Normal vs Free Spins)
    turn_multiplier_sum = sum(multiplier_values_found)
    
    if st.session_state.is_in_bonus:
        # FREE SPINS MULTIPLIER RULES:
        if base_spin_win > 0 and turn_multiplier_sum > 0:
            # If we win and find orbs, add them permanently to our global multiplier pool
            st.session_state.global_bonus_multiplier += turn_multiplier_sum
            win_breakdown_messages.append(f"⭐ Global Multiplier increased by +{turn_multiplier_sum}x!")
        
        # In free spins, wins are always multiplied by the current accumulated global pool
        st.session_state.active_multiplier = st.session_state.global_bonus_multiplier
        final_total_win = base_spin_win * st.session_state.active_multiplier if base_spin_win > 0 else 0
        st.session_state.total_bonus_win += final_total_win
    else:
        # NORMAL SPIN MULTIPLIER RULES:
        st.session_state.active_multiplier = turn_multiplier_sum if turn_multiplier_sum > 0 else 1
        if base_spin_win > 0 and turn_multiplier_sum > 0:
            final_total_win = base_spin_win * turn_multiplier_sum
            win_breakdown_messages.append(f"🔥 Multiplier Orbs Combined: {turn_multiplier_sum}x Boost!")
        else:
            final_total_win = base_spin_win

    # Update global app balance tracking
    st.session_state.last_win = final_total_win
    st.session_state.balance += final_total_win
    
    # Check if the bonus round has ended
    if st.session_state.is_in_bonus and st.session_state.free_spins_left <= 0:
        st.session_state.is_in_bonus = False
        win_breakdown_messages.append(f"🛑 BONUS ROUND COMPLETED! Total Bonus Payout: +${st.session_state.total_bonus_win}")
        
    return win_breakdown_messages

# --- VISUAL DASHBOARD INTERFACE ---

# Display bonus alerts at the top of the interface
if st.session_state.is_in_bonus:
    st.warning(f"🎰 FREE SPINS MODE ACTIVATED: {st.session_state.free_spins_left} SPINS REMAINING")

# Scoreboard displays
stat_col1, stat_col2, stat_col3 = st.columns(3)
with stat_col1:
    st.metric(label="Balance", value=f"${st.session_state.balance}")
with stat_col2:
    label_text = "Total Bonus Win" if st.session_state.is_in_bonus else "Last Spin Win"
    value_text = f"${st.session_state.total_bonus_win}" if st.session_state.is_in_bonus else f"${st.session_state.last_win}"
    st.metric(label=label_text, value=value_text)
with stat_col3:
    label_mult = "Global Multiplier Pool" if st.session_state.is_in_bonus else "Last Multiplier Hit"
    st.metric(label=label_mult, value=f"{st.session_state.active_multiplier}x")

st.divider()

# Render the 6x5 slot machine grid canvas using mobile-safe text columns
st.write("### 🎰 THE REELS")
for row in st.session_state.grid:
    cols = st.columns(6)
    for col_idx in range(6):
        with cols[col_idx]:
            st.write(f"## {row[col_idx]}")

st.divider()

# Betting system controls
bet_selection = st.radio(
    "Select Bet Size:", [20, 50, 100, 500], 
    horizontal=True, 
    disabled=st.session_state.is_in_bonus
)

# Operational execution loops
if st.session_state.balance < bet_selection and not st.session_state.is_in_bonus:
    st.error("❌ Insufficient credits for this bet size!")
    if st.button("🔄 Refill $5,000 Play Money"):
        st.session_state.balance = 5000
        st.session_state.last_win = 0
        st.session_state.is_in_bonus = False
        st.session_state.free_spins_left = 0
        st.rerun()
else:
    # Button adjustments depending on current active state
    button_label = "🔥 PRESS TO EXECUTE FREE SPIN" if st.session_state.is_in_bonus else "🚀 SPIN THE REELS"
    
    if st.button(button_label, use_container_width=True):
        win_reports = spin_engine(bet_selection)
        
        # Display feedback animations
        if st.session_state.last_win > 0:
            st.balloons()
            st.success(f"🎉 WINNER! Total Payout: +${st.session_state.last_win}")
        
        for report in win_reports:
            st.write(f"• {report}")
            
        st.rerun()
        
