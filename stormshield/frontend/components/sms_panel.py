"""
SMS Alert Subscription Panel for StormShield AI.
"""
from __future__ import annotations

import httpx
import streamlit as st
from frontend.config import BACKEND_URL

def render_sms_panel() -> None:
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h4 style="margin:0; background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🔔 SMS Alert System</h4>
            <div style="font-size: 13px; color: #94a3b8;">Subscribe to real-time flood notifications and emergency updates for Montgomery, AL</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 🛡️ Flood Alert System Legend")
        st.write("StormShield AI monitors river levels 24/7. Here is what our automated SMS alerts represent:")
        
        with st.container(border=True):
            cols = st.columns([0.15, 0.85])
            cols[0].markdown("### 🔴")
            with cols[1]:
                st.markdown("**RED ALERT (Emergency)**")
                st.caption("Predicted water levels >= Flood Stage (8.0 ft). High risk of flooding. Evacuation may be necessary.")
        
        with st.container(border=True):
            cols = st.columns([0.15, 0.85])
            cols[0].markdown("### 🟡")
            with cols[1]:
                st.markdown("**YELLOW ALERT (Warning)**")
                st.caption("Water levels rising rapidly (> 2.0 ft in 15 mins) or approaching flood stage. Stay vigilant.")
        
        with st.container(border=True):
            cols = st.columns([0.15, 0.85])
            cols[0].markdown("### 🟢")
            with cols[1]:
                st.markdown("**GREEN ALERT (Normal)**")
                st.caption("All clear. Water levels are within safe limits. System is in continuous monitoring mode.")

    with col2:
        st.markdown("### Secure Alert Subscription")
        
        # OTP Flow State Management
        if "otp_step" not in st.session_state:
            st.session_state.otp_step = 1
        
        if st.session_state.otp_step == 1:
            phone = st.text_input("Mobile Number", placeholder="e.g., 9988776655", key="sms_phone_input")
            st.markdown("<div style='color: #fca311; font-size: 13px; font-weight: 500; margin-bottom: 10px;'>🛡️ We track Montgomery flood risks and send real-time alerts. Verification call required.</div>", unsafe_allow_html=True)
            
            if st.button("🚀 Get Verification Call", type="primary", use_container_width=True):
                if phone and len(phone) >= 10:
                    try:
                        with st.spinner("Connecting to secure gateway..."):
                            resp = httpx.post(f"{BACKEND_URL}/api/alert/send-otp", json={"phone": phone}, timeout=30)
                            if resp.status_code == 200:
                                res = resp.json()
                                if res.get("status") == "success":
                                    st.session_state.otp_phone = phone
                                    st.session_state.otp_session = res.get("session_id")
                                    st.session_state.otp_step = 2
                                    st.rerun()
                                elif res.get("message") == "already_registered":
                                    st.info("ℹ️ You are already registered for StormShield alerts!")
                                else:
                                    st.error(f"❌ API Error: {res.get('message')}")
                            else:
                                st.error(f"❌ Service unreachable. Error code: {resp.status_code}")
                    except Exception as e:
                        st.error(f"⚠️ Connection Error: {e}")
                else:
                    st.warning("⚠️ Please enter your 10-digit mobile number.")
        
        elif st.session_state.otp_step == 2:
            st.markdown(f"<div style='color: #10b981; font-weight: 700; font-size: 15px;'>📞 Call triggered for {st.session_state.otp_phone}</div>", unsafe_allow_html=True)
            st.markdown("<div style='color: #cbd5e1; font-size: 12px; margin-bottom: 15px;'>Please answer the call to receive your 6-digit verification code.</div>", unsafe_allow_html=True)
            
            otp_code = st.text_input("Enter Code from Call", placeholder="123456", key="otp_input")
            
            def handle_verification():
                if not st.session_state.otp_input:
                    st.session_state.otp_error = "Please enter the code."
                    return
                
                try:
                    payload = {
                        "phone": st.session_state.otp_phone,
                        "session_id": st.session_state.otp_session,
                        "otp": st.session_state.otp_input
                    }
                    resp = httpx.post(f"{BACKEND_URL}/api/alert/verify-otp", json=payload, timeout=30)
                    if resp.status_code == 200:
                        res = resp.json()
                        if res.get("status") == "success":
                            st.session_state.verify_success = True
                            st.session_state.otp_step = 3 # Success step
                        else:
                            st.session_state.otp_error = f"Verification Failed: {res.get('message')}"
                    else:
                        st.session_state.otp_error = f"Backend Error (HTTP {resp.status_code})"
                except Exception as e:
                    st.session_state.otp_error = f"Error: {e}"

            if st.button("✅ Verify & Subscribe", type="primary", use_container_width=True, on_click=handle_verification):
                pass # Logic handled in callback

            if "otp_error" in st.session_state and st.session_state.otp_error:
                st.error(f"❌ {st.session_state.otp_error}")
                st.session_state.otp_error = None

        elif st.session_state.otp_step == 3:
            st.success("🎉 Verification Successful! You are now subscribed.")
            st.balloons()
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
            if st.button("Done", use_container_width=True):
                # Clean up and reset
                st.session_state.otp_step = 1
                if 'otp_input' in st.session_state:
                    del st.session_state['otp_input']
                if 'otp_phone' in st.session_state:
                    del st.session_state['otp_phone']
                st.rerun()
            
            # Using custom styling for the change number button to make it visible
            st.markdown("""
                <style>
                div[data-testid="stButton"] button:not([kind="primary"]) {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: white !important;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("⬅️ Change Phone Number", use_container_width=True):
                st.session_state.otp_step = 1
                st.rerun()

    is_dark = st.session_state.get("theme", "dark") == "dark"
    policy_bg = "rgba(30, 41, 59, 0.6)" if is_dark else "rgba(255, 255, 255, 0.7)"
    policy_border = "rgba(255, 255, 255, 0.1)" if is_dark else "#e2e8f0"
    policy_title = "#f8fafc" if is_dark else "#1e293b"
    policy_text = "#cbd5e1" if is_dark else "#64748b"
    
    st.markdown("---")
    st.markdown(f"<h5 style='color: {policy_title};'>🛡️ Alert Policy & Privacy</h5>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: {policy_text}; font-size: 13px; background: {policy_bg}; padding: 15px; border-radius: 10px; border: 1px solid {policy_border};'>StormShield AI serves the Montgomery community. We only send critical alerts related to flood risks. Your data is never shared.</div>", unsafe_allow_html=True)
