import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'EMAIL' | 'OTP'>('EMAIL');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/request-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to request OTP');
      
      setStep('OTP');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code: otp })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invalid OTP code');
      
      // Save token and redirect
      localStorage.setItem('ascs_token', data.access_token);
      router.push('/');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      fontFamily: 'Inter, Poppins, sans-serif',
      backgroundColor: '#f4f6f9',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <Head>
        <title>Login - ASCS</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap" rel="stylesheet" />
      </Head>

      <div style={{
        background: '#ffffff',
        padding: '40px',
        borderRadius: '16px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.05)',
        width: '400px',
        textAlign: 'center',
        border: '1px solid #e2e8f0'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '12px',
          marginBottom: '24px'
        }}>
          <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Department_of_Education_%28DepEd%29.svg/1024px-Department_of_Education_%28DepEd%29.svg.png" alt="DepEd Logo" style={{ height: '60px' }} />
        </div>

        <h1 style={{
          fontFamily: 'Poppins, sans-serif',
          fontWeight: 700,
          fontSize: '24px',
          color: '#0038A8',
          marginBottom: '8px',
          marginTop: 0
        }}>
          ASCS Portal
        </h1>
        <p style={{
          color: '#64748b',
          fontSize: '14px',
          marginBottom: '32px'
        }}>
          {step === 'EMAIL' ? 'Enter your email to receive a login code.' : `Enter the 6-digit code sent to ${email}`}
        </p>

        {error && (
          <div style={{
            backgroundColor: '#fee2e2',
            color: '#b91c1c',
            padding: '12px',
            borderRadius: '8px',
            fontSize: '13px',
            marginBottom: '24px',
            fontWeight: 500
          }}>
            {error}
          </div>
        )}

        {step === 'EMAIL' ? (
          <form onSubmit={handleRequestOTP} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <input
              type="email"
              placeholder="name@school.edu.ph"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '14px 16px',
                fontSize: '15px',
                outline: 'none',
                width: '100%',
                boxSizing: 'border-box'
              }}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                backgroundColor: '#0038A8',
                color: '#ffffff',
                padding: '14px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '15px',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                boxShadow: '0 4px 6px rgba(0, 56, 168, 0.2)',
                transition: 'all 0.2s'
              }}
            >
              {loading ? 'Sending...' : 'Send Login Code'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <input
              type="text"
              placeholder="123456"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              required
              maxLength={6}
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '14px 16px',
                fontSize: '24px',
                letterSpacing: '8px',
                textAlign: 'center',
                outline: 'none',
                width: '100%',
                boxSizing: 'border-box',
                fontFamily: 'monospace'
              }}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                backgroundColor: '#0038A8',
                color: '#ffffff',
                padding: '14px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '15px',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                boxShadow: '0 4px 6px rgba(0, 56, 168, 0.2)',
                transition: 'all 0.2s'
              }}
            >
              {loading ? 'Verifying...' : 'Verify & Login'}
            </button>
            <button
              type="button"
              onClick={() => { setStep('EMAIL'); setOtp(''); setError(''); }}
              style={{
                background: 'none',
                border: 'none',
                color: '#64748b',
                fontSize: '13px',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              Use a different email
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
