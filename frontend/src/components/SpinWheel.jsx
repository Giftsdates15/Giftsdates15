import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { api } from "../lib/api";
import { useApp } from "../context/AppContext";
import { Crown, Sparkles, Coins, Gift, PartyPopper } from "lucide-react";

// 8 sectors — order & indices MUST match backend SPIN_PRIZES
const PRIZES = [
  { label: "Try Again", type: "none" },
  { label: "Premium-Lite", type: "premium_lite" },
  { label: "Try Again", type: "none" },
  { label: "Premium", type: "premium" },
  { label: "Try Again", type: "none" },
  { label: "VIP", type: "vip" },
  { label: "Try Again", type: "none" },
  { label: "10 Coins", type: "coins" },
];
const COLORS = ["#3f3f46", "#38bdf8", "#3f3f46", "#f59e0b", "#3f3f46", "#ef4444", "#3f3f46", "#f59e0b"];
const SEG = 45;
const GRAD = `conic-gradient(from -22.5deg, ${COLORS.map((c, i) => `${c} ${i * SEG}deg ${(i + 1) * SEG}deg`).join(", ")})`;

const TIER_NAME = { premium_lite: "Premium-Lite", premium: "Premium", vip: "VIP" };

function SectorLabel({ p }) {
  return (
    <div className="absolute left-1/2 top-2 -translate-x-1/2 w-16 text-center leading-tight">
      <div className={`font-semibold ${p.label.length > 8 ? "text-[9px]" : "text-[11px]"} text-white drop-shadow`}>
        {p.type === "coins" ? "10 🪙" : p.type === "none" ? "—" : p.label}
      </div>
    </div>
  );
}

/**
 * Controlled one-time welcome wheel.
 * Props:
 *  - open: boolean
 *  - onClose(prizeOrNull): called when user finishes (spun) or dismisses (closed)
 *  - userName: string for the personalized welcome message
 */
export const SpinWheel = ({ open, onClose, userName }) => {
  const { refreshUser } = useApp();
  const [rot, setRot] = useState(0);
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const [done, setDone] = useState(false); // becomes true once a spin has been consumed

  const doSpin = async () => {
    if (spinning || result) return;
    setSpinning(true);
    try {
      const { data } = await api.post("/spin/claim");
      const p = data.prize;
      const target = 360 * 6 + (360 - (p.index || 0) * SEG);
      setRot(target);
      setTimeout(async () => {
        setResult(p);
        setDone(true);
        setSpinning(false);
        await refreshUser();
      }, 4300);
    } catch (e) {
      setSpinning(false);
      setDone(true); // if backend says already used, don't allow retry
    }
  };

  const finish = () => { onClose && onClose(result); };

  // Dismissing (X or overlay) before spinning permanently disables the wheel.
  const handleOpenChange = async (o) => {
    if (o) return;
    if (!done && !spinning) {
      try { await api.post("/spin/dismiss"); } catch { /* ignore */ }
      await refreshUser();
    }
    onClose && onClose(result);
  };

  const welcome = () => {
    const name = userName ? `${userName}, ` : "";
    if (!result) return "";
    if (result.type === "coins") {
      return `Congratulations, ${name}you won 10 Coins! They've been added to your wallet.`;
    }
    if (TIER_NAME[result.type]) {
      return `Congratulations! You won a 7-day ${TIER_NAME[result.type]} account!`;
    }
    return `Welcome to GiftsDates, ${name}! Explore profiles, send gifts and start connecting.`;
  };

  const ResultIcon = result?.type === "coins" ? Coins
    : result?.type === "vip" ? Crown
    : result?.type === "premium" ? Crown
    : result?.type === "premium_lite" ? Sparkles
    : PartyPopper;

  const isWin = result && result.type !== "none";

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="bg-[#141019] border-white/10 text-white sm:max-w-md" data-testid="spin-dialog">
        <DialogHeader>
          <DialogTitle className="font-serif-luxe text-2xl flex items-center gap-2">
            <Sparkles size={20} className="text-amber-300" /> Spin to Win — Welcome Gift
          </DialogTitle>
        </DialogHeader>
        <p className="text-sm text-slate-400 -mt-1">One free spin, just for joining. Good luck!</p>

        <div className="relative mx-auto my-4" style={{ width: 300, height: 300 }} data-testid="spin-wheel">
          <div className="absolute left-1/2 -translate-x-1/2 -top-1 z-20"
            style={{ width: 0, height: 0, borderLeft: "14px solid transparent", borderRight: "14px solid transparent", borderTop: "22px solid #fbbf24" }} />
          <div className="absolute inset-0 rounded-full border-4 border-amber-400/60 shadow-[0_0_40px_rgba(245,158,11,0.35)] pointer-events-none"
            style={{ background: GRAD, transform: `rotate(${rot}deg)`, transition: "transform 4.2s cubic-bezier(0.16,1,0.3,1)" }}>
            {PRIZES.map((p, i) => (
              <div key={i} className="absolute inset-0" style={{ transform: `rotate(${i * SEG}deg)` }}>
                <SectorLabel p={p} />
              </div>
            ))}
          </div>
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-[#141019] border-4 border-amber-400/70 z-10 flex items-center justify-center">
            <Crown size={18} className="text-amber-300" />
          </div>
        </div>

        {!result ? (
          <Button data-testid="spin-go-btn" onClick={doSpin} disabled={spinning}
            className="w-full rose-btn text-white border-0 h-12 text-base">
            <Gift size={18} className="me-2" /> {spinning ? "Spinning…" : "Spin the Wheel"}
          </Button>
        ) : (
          <div data-testid="spin-result" className="text-center space-y-3">
            <div className={`rounded-2xl border p-4 ${isWin ? "border-amber-500/40 bg-amber-500/10" : "border-white/10 bg-white/5"}`}>
              <div className="flex justify-center mb-2"><ResultIcon size={30} className={isWin ? "text-amber-300" : "text-slate-300"} /></div>
              <div className="font-serif-luxe text-xl leading-snug">{welcome()}</div>
              {result.expires_at && (
                <div className="text-xs text-emerald-300 mt-2" data-testid="spin-expiry">
                  Expires on {new Date(result.expires_at).toLocaleString()}
                </div>
              )}
            </div>
            <Button data-testid="spin-continue-btn" onClick={finish} className="w-full rose-btn text-white border-0 h-12 text-base">
              Continue
            </Button>
          </div>
        )}
        <p className="text-center text-[11px] text-slate-500">This welcome spin can only be used once.</p>
      </DialogContent>
    </Dialog>
  );
};

export default SpinWheel;
