🚨 *CrashLens Token Waste Report* 🚨
📊 *Analysis Date:* 2025-08-04 22:59:53

📋 *Report Summary:*
• 💰 *Total AI Spend:* $0.09
• 🔥 *Potential Savings:* $0.07
• 🎯 *Wasted Tokens:* 1,414
• ⚠️ *Issues Found:* 8
• 📈 *Traces Analyzed:* 12

📢 *Fallback Failure* • 5 traces • $0.07 wasted
   💡 *Fix:* remove redundant fallbacks
   🎯 *Wasted tokens:* 1,275
   🔗 *Traces (5):* `demo_fallback_01, demo_fallback_02, demo_fallback_03, demo_fallback_04, demo_fallback_05`

❓ *Overkill Model* • 2 traces • $0.0007 wasted
   💡 *Fix:* optimize usage
   🎯 *Wasted tokens:* 31
   🔗 *Traces (2):* `demo_overkill_01, demo_overkill_02`

🔄 *Retry Loop* • 1 traces • $0.0002 wasted
   💡 *Fix:* exponential backoff
   🎯 *Wasted tokens:* 108
   🔗 *Traces (1):* `demo_retry_01`


🏆 *Top Expensive Traces:*
• #1 → `demo_norm_03` → gpt-4 → $0.03
• #2 → `demo_norm_04` → gpt-4 → $0.02
• #3 → `demo_fallback_05` → gpt-3.5-turbo → $0.02

🤖 *Cost by Model:*
• gpt-4 → $0.09 (99%)
• gpt-3.5-turbo → $0.0012 (1%)

💡 *Next Steps:*
• Run `crashlens --detailed` for grouped JSON reports
• Review trace patterns to optimize model routing
• Implement suggested fixes to reduce token waste
