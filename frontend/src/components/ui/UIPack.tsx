import React from 'react';
import { cn } from '../../lib/utils/cn';
import { Loader2 } from 'lucide-react';

// --- BUTTON PRIMITIVE ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'white';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
  icon?: React.ElementType;
}

export function Button({ 
  className, 
  variant = 'primary', 
  size = 'md', 
  isLoading, 
  icon: Icon,
  children, 
  ...props 
}: ButtonProps) {
  const baseStyles = "inline-flex items-center justify-center gap-2 font-bold uppercase tracking-wider transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer";
  
  const variants = {
    primary: "bg-black text-white hover:bg-zinc-800 shadow-lg shadow-black/5 border border-black",
    secondary: "bg-white text-black border border-[#eeeeee] hover:bg-zinc-50 shadow-sm",
    outline: "bg-transparent border border-[#eeeeee] text-zinc-500 hover:text-black hover:border-black",
    ghost: "bg-transparent text-zinc-400 hover:text-black hover:bg-zinc-50",
    danger: "bg-rose-50 text-rose-500 border border-rose-100 hover:bg-rose-500 hover:text-white",
    white: "bg-white text-black border border-[#eeeeee] hover:shadow-md"
  };

  const sizes = {
    sm: "h-8 px-3 text-[9px] rounded-lg",
    md: "h-11 px-5 text-[10px] rounded-xl",
    lg: "h-13 px-7 text-[11px] rounded-2xl",
    xl: "h-15 px-9 text-[12px] rounded-2xl"
  };

  return (
    <button className={cn(baseStyles, variants[variant], sizes[size], className)} disabled={isLoading || props.disabled} {...props}>
      {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : Icon && <Icon className="w-4 h-4" />}
      {children}
    </button>
  );
}

// --- CARD PRIMITIVE ---
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'glass';
}

export function Card({ className, variant = 'default', ...props }: CardProps) {
  const baseStyles = "rounded-2xl transition-all duration-300";
  const variants = {
    default: "bg-white border border-[#eeeeee] shadow-sm",
    elevated: "bg-white border border-[#eeeeee] shadow-xl hover:shadow-2xl hover:translate-y-[-2px]",
    glass: "bg-white/80 backdrop-blur-xl border border-white/40 shadow-lg"
  };

  return <div className={cn(baseStyles, variants[variant], className)} {...props} />;
}

// --- BADGE PRIMITIVE ---
interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'premium';
  className?: string;
}

export function Badge({ children, variant = 'neutral', className }: BadgeProps) {
  const baseStyles = "inline-flex items-center px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider border transition-all shadow-sm";
  const variants = {
    success: "bg-emerald-50 text-emerald-600 border-emerald-100",
    warning: "bg-amber-50 text-amber-600 border-amber-100",
    error: "bg-rose-50 text-rose-600 border-rose-100",
    info: "bg-blue-50 text-blue-600 border-blue-100",
    neutral: "bg-zinc-50 text-zinc-500 border-[#eeeeee]",
    premium: "bg-black text-white border-black"
  };

  return (
    <div className={cn(baseStyles, variants[variant], className)}>
      {children}
    </div>
  );
}

