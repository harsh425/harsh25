import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import SignatureCanvas from 'react-signature-canvas';
import { toast } from 'sonner';
import { CheckCircle, PenTool, Type, Upload, Eraser } from 'lucide-react';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SignContract = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [signatureType, setSignatureType] = useState('draw'); // 'draw', 'type', 'upload'
  const [typedSignature, setTypedSignature] = useState('');
  const [uploadedSignature, setUploadedSignature] = useState(null);
  const signatureRef = useRef(null);

  useEffect(() => {
    fetchContract();
  }, [token]);

  const fetchContract = async () => {
    try {
      const response = await axios.get(`${API}/contracts/sign/${token}`);
      setContract(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Contract not found');
      setTimeout(() => navigate('/login'), 2000);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    if (signatureRef.current) {
      signatureRef.current.clear();
    }
  };

  const handleUploadSignature = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setUploadedSignature(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const getSignatureData = () => {
    if (signatureType === 'draw') {
      if (signatureRef.current && !signatureRef.current.isEmpty()) {
        return signatureRef.current.toDataURL();
      }
      return null;
    } else if (signatureType === 'type') {
      if (!typedSignature.trim()) return null;
      const canvas = document.createElement('canvas');
      canvas.width = 400;
      canvas.height = 100;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = '36px Dancing Script, cursive';
      ctx.fillStyle = 'black';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(typedSignature, canvas.width / 2, canvas.height / 2);
      return canvas.toDataURL();
    } else if (signatureType === 'upload') {
      return uploadedSignature;
    }
    return null;
  };

  const handleSign = async () => {
    const signatureData = getSignatureData();
    if (!signatureData) {
      toast.error('Please provide a signature');
      return;
    }

    setSigning(true);
    try {
      // Get IP address (simplified)
      const ipResponse = await fetch('https://api.ipify.org?format=json');
      const ipData = await ipResponse.json();

      await axios.post(`${API}/contracts/sign/${token}`, {
        signature_data: signatureData,
        signature_type: signatureType,
        ip_address: ipData.ip || 'unknown'
      });

      toast.success('Contract signed successfully!');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sign contract');
    } finally {
      setSigning(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-900 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading contract...</p>
        </div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Contract Not Found</h2>
          <p className="text-slate-600">This contract link may be invalid or expired.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4" data-testid="sign-contract-page">
      <div className="max-w-4xl mx-auto">
        <div className="card p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-blue-900 rounded-sm flex items-center justify-center">
              <PenTool className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Employment Contract</h1>
              <p className="text-slate-600">Please review and sign</p>
            </div>
          </div>

          {/* Contract Details */}
          <div className="bg-slate-50 p-6 rounded-sm mb-6">
            <h2 className="text-xl font-semibold mb-4 text-slate-900">{contract.title}</h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="label">Employee Name</p>
                <p className="font-medium">{contract.employee?.full_name}</p>
              </div>
              <div>
                <p className="label">Employee ID</p>
                <p className="mono font-medium">{contract.employee?.employee_id}</p>
              </div>
              <div>
                <p className="label">Position</p>
                <p className="font-medium">{contract.employee?.position}</p>
              </div>
              <div>
                <p className="label">Department</p>
                <p className="font-medium">{contract.employee?.department}</p>
              </div>
            </div>
            <div>
              <p className="label">Contract Terms</p>
              <p className="whitespace-pre-wrap">{contract.description}</p>
            </div>
          </div>

          {/* Signature Section */}
          <div className="border-t border-slate-200 pt-6">
            <h3 className="text-xl font-semibold mb-4 text-slate-900">Your Signature</h3>

            {/* Signature Type Selector */}
            <div className="flex gap-3 mb-6" data-testid="signature-type-selector">
              <button
                onClick={() => setSignatureType('draw')}
                data-testid="signature-type-draw"
                className={`flex-1 py-3 px-4 rounded-sm border-2 transition ${
                  signatureType === 'draw'
                    ? 'border-blue-900 bg-blue-50 text-blue-900'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <PenTool className="w-5 h-5 mx-auto mb-1" />
                <span className="text-sm font-medium">Draw</span>
              </button>
              <button
                onClick={() => setSignatureType('type')}
                data-testid="signature-type-type"
                className={`flex-1 py-3 px-4 rounded-sm border-2 transition ${
                  signatureType === 'type'
                    ? 'border-blue-900 bg-blue-50 text-blue-900'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <Type className="w-5 h-5 mx-auto mb-1" />
                <span className="text-sm font-medium">Type</span>
              </button>
              <button
                onClick={() => setSignatureType('upload')}
                data-testid="signature-type-upload"
                className={`flex-1 py-3 px-4 rounded-sm border-2 transition ${
                  signatureType === 'upload'
                    ? 'border-blue-900 bg-blue-50 text-blue-900'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <Upload className="w-5 h-5 mx-auto mb-1" />
                <span className="text-sm font-medium">Upload</span>
              </button>
            </div>

            {/* Draw Signature */}
            {signatureType === 'draw' && (
              <div data-testid="draw-signature-area">
                <div className="bg-white border-2 border-slate-300 rounded-sm mb-3">
                  <SignatureCanvas
                    ref={signatureRef}
                    canvasProps={{
                      className: 'signature-canvas w-full h-48',
                      'data-testid': 'signature-canvas'
                    }}
                  />
                </div>
                <button
                  onClick={handleClear}
                  data-testid="clear-signature-button"
                  className="flex items-center gap-2 text-slate-600 hover:text-slate-900"
                >
                  <Eraser className="w-4 h-4" /> Clear Signature
                </button>
              </div>
            )}

            {/* Type Signature */}
            {signatureType === 'type' && (
              <div data-testid="type-signature-area">
                <input
                  type="text"
                  data-testid="type-signature-input"
                  className="input-field text-2xl"
                  style={{ fontFamily: 'Dancing Script, cursive' }}
                  value={typedSignature}
                  onChange={(e) => setTypedSignature(e.target.value)}
                  placeholder="Type your full name..."
                />
                {typedSignature && (
                  <div className="mt-4 p-4 bg-white border-2 border-slate-300 rounded-sm text-center">
                    <p className="text-4xl" style={{ fontFamily: 'Dancing Script, cursive' }}>
                      {typedSignature}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Upload Signature */}
            {signatureType === 'upload' && (
              <div data-testid="upload-signature-area">
                <input
                  type="file"
                  data-testid="upload-signature-input"
                  className="input-field"
                  accept="image/*"
                  onChange={handleUploadSignature}
                />
                {uploadedSignature && (
                  <div className="mt-4 p-4 bg-white border-2 border-slate-300 rounded-sm">
                    <img src={uploadedSignature} alt="Signature" className="max-h-32 mx-auto" />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sign Button */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <Button
              onClick={handleSign}
              data-testid="sign-contract-button"
              disabled={signing}
              className="btn-secondary w-full py-4 text-lg flex items-center justify-center gap-2"
            >
              {signing ? (
                'Signing...'
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" /> Sign Contract
                </>
              )}
            </Button>
            <p className="text-sm text-slate-500 text-center mt-3">
              By signing, you agree to the terms and conditions outlined above.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignContract;
