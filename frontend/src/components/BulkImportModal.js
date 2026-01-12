import React, { useState } from 'react';
import axios from 'axios';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import { toast } from 'sonner';
import { Upload, Download, FileSpreadsheet, AlertCircle, CheckCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BulkImportModal = ({ isOpen, onClose, onSuccess }) => {
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [results, setResults] = useState(null);

  const downloadTemplate = () => {
    const template = [
      {
        employee_number: 'EMP001',
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-15',
        gender: 'Male',
        marital_status: 'Single',
        email: 'john.doe@company.com',
        phone_number: '+254700000000',
        mpesa_number: '+254700000000',
        kra_pin: 'A000000000A',
        nssf_number: '1234567890',
        shif_number: 'SH000000000',
        emergency_contact_name: 'Jane Doe',
        emergency_contact_phone: '+254700000001',
        emergency_contact_relationship: 'Spouse',
        emergency_contact_email: 'jane.doe@email.com',
        bank_account_name: 'John Doe',
        bank_name: 'Equity Bank',
        bank_branch_name: 'Nairobi Branch',
        bank_branch_code: '068',
        bank_account_number: '0123456789',
        department: 'Engineering',
        position: 'Software Engineer',
        employment_type: 'Full-time',
        contract_start_date: '2025-01-01',
        contract_end_date: '',
        manager_id: ''
      }
    ];

    const ws = XLSX.utils.json_to_sheet(template);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Employees');
    XLSX.writeFile(wb, 'employee_import_template.xlsx');
    toast.success('Template downloaded');
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResults(null);
    }
  };

  const parseFile = (file) => {
    return new Promise((resolve, reject) => {
      const fileExtension = file.name.split('.').pop().toLowerCase();

      if (fileExtension === 'csv') {
        Papa.parse(file, {
          header: true,
          complete: (results) => resolve(results.data),
          error: (error) => reject(error)
        });
      } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            const jsonData = XLSX.utils.sheet_to_json(firstSheet);
            resolve(jsonData);
          } catch (error) {
            reject(error);
          }
        };
        reader.onerror = (error) => reject(error);
        reader.readAsArrayBuffer(file);
      } else {
        reject(new Error('Unsupported file format. Please use CSV or Excel files.'));
      }
    });
  };

  const handleImport = async () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setImporting(true);
    try {
      const parsedData = await parseFile(file);
      
      // Validate and transform data
      const employees = parsedData.filter(row => row.employee_number && row.first_name).map(row => ({
        employee_number: String(row.employee_number),
        first_name: String(row.first_name),
        last_name: String(row.last_name),
        date_of_birth: String(row.date_of_birth || ''),
        gender: String(row.gender || ''),
        marital_status: String(row.marital_status || ''),
        email: String(row.email),
        phone_number: String(row.phone_number || ''),
        mpesa_number: String(row.mpesa_number || ''),
        kra_pin: String(row.kra_pin || ''),
        nssf_number: String(row.nssf_number || ''),
        shif_number: String(row.shif_number || ''),
        emergency_contact_name: String(row.emergency_contact_name || ''),
        emergency_contact_phone: String(row.emergency_contact_phone || ''),
        emergency_contact_relationship: String(row.emergency_contact_relationship || ''),
        emergency_contact_email: String(row.emergency_contact_email || ''),
        bank_account_name: String(row.bank_account_name || ''),
        bank_name: String(row.bank_name || ''),
        bank_branch_name: String(row.bank_branch_name || ''),
        bank_branch_code: String(row.bank_branch_code || ''),
        bank_account_number: String(row.bank_account_number || ''),
        department: String(row.department || ''),
        position: String(row.position || ''),
        employment_type: String(row.employment_type || 'Full-time'),
        contract_start_date: String(row.contract_start_date || ''),
        contract_end_date: String(row.contract_end_date || ''),
        manager_id: String(row.manager_id || '')
      }));

      if (employees.length === 0) {
        toast.error('No valid employee data found in file');
        return;
      }

      // Send to backend
      const response = await axios.post(`${API}/employees/bulk-import`, { employees });
      setResults(response.data);
      
      if (response.data.success_count > 0) {
        toast.success(`Successfully imported ${response.data.success_count} employees`);
        onSuccess();
      }
      
      if (response.data.failed_count > 0) {
        toast.warning(`${response.data.failed_count} employees failed to import`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to import employees');
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResults(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl" data-testid="bulk-import-modal">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold flex items-center gap-2">
            <FileSpreadsheet className="w-6 h-6" />
            Bulk Employee Import
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Download Template */}
          <div className="bg-blue-50 border border-blue-200 rounded-sm p-4">
            <p className="text-sm text-blue-900 mb-3">
              <strong>Step 1:</strong> Download the template and fill in your employee data
            </p>
            <button
              onClick={downloadTemplate}
              data-testid="download-template-button"
              className="flex items-center gap-2 text-blue-900 hover:underline font-medium"
            >
              <Download className="w-4 h-4" />
              Download Excel Template
            </button>
          </div>

          {/* Upload File */}
          <div>
            <label className="label">Step 2: Upload Completed File</label>
            <input
              type="file"
              data-testid="bulk-import-file-input"
              className="input-field"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
            />
            <p className="text-sm text-slate-500 mt-1">
              Accepted formats: CSV, Excel (.xlsx, .xls)
            </p>
            {file && (
              <div className="mt-2 flex items-center gap-2 text-sm text-emerald-600">
                <CheckCircle className="w-4 h-4" />
                Selected: {file.name}
              </div>
            )}
          </div>

          {/* Results */}
          {results && (
            <div className="bg-slate-50 border border-slate-200 rounded-sm p-4">
              <h4 className="font-semibold mb-2">Import Results</h4>
              <div className="space-y-2 text-sm">
                <p className="text-emerald-600">
                  <CheckCircle className="w-4 h-4 inline mr-1" />
                  Successfully imported: {results.success_count}
                </p>
                {results.failed_count > 0 && (
                  <div>
                    <p className="text-red-600">
                      <AlertCircle className="w-4 h-4 inline mr-1" />
                      Failed to import: {results.failed_count}
                    </p>
                    {results.errors && (
                      <ul className="ml-5 mt-2 space-y-1 text-slate-600">
                        {results.errors.map((error, index) => (
                          <li key={index} className="text-xs">• {error}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Required Fields Info */}
          <div className="bg-slate-50 border border-slate-200 rounded-sm p-4">
            <h4 className="font-semibold mb-2 text-sm">Required Fields (26 total)</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div>
                <p className="font-semibold text-slate-700 mt-2">Personal:</p>
                <ul className="space-y-1">
                  <li>• employee_number</li>
                  <li>• first_name, last_name</li>
                  <li>• date_of_birth, gender</li>
                  <li>• marital_status</li>
                </ul>
                <p className="font-semibold text-slate-700 mt-2">Contact:</p>
                <ul className="space-y-1">
                  <li>• email, phone_number</li>
                  <li>• mpesa_number</li>
                </ul>
                <p className="font-semibold text-slate-700 mt-2">Statutory:</p>
                <ul className="space-y-1">
                  <li>• kra_pin, nssf_number</li>
                  <li>• shif_number</li>
                </ul>
              </div>
              <div>
                <p className="font-semibold text-slate-700 mt-2">Emergency:</p>
                <ul className="space-y-1">
                  <li>• emergency_contact_name</li>
                  <li>• emergency_contact_phone</li>
                  <li>• emergency_contact_relationship</li>
                  <li>• emergency_contact_email</li>
                </ul>
                <p className="font-semibold text-slate-700 mt-2">Bank:</p>
                <ul className="space-y-1">
                  <li>• bank_account_name</li>
                  <li>• bank_name, bank_branch_name</li>
                  <li>• bank_branch_code</li>
                  <li>• bank_account_number</li>
                </ul>
                <p className="font-semibold text-slate-700 mt-2">Employment:</p>
                <ul className="space-y-1">
                  <li>• department, position</li>
                  <li>• contract_start_date</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              onClick={handleImport}
              data-testid="import-employees-button"
              disabled={!file || importing}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              <Upload className="w-4 h-4" />
              {importing ? 'Importing...' : 'Import Employees'}
            </Button>
            <Button
              onClick={handleClose}
              className="btn-secondary flex-1"
              disabled={importing}
            >
              {results ? 'Close' : 'Cancel'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default BulkImportModal;
