export interface InvoiceItem {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  price: number;
  status: 'normal' | 'credited' | 'returned';
}

export interface Invoice {
  invoice_id: number;
  vendor: string;
  date: string;
  totalAmount: number;
  confirmedAt: string;
  items: InvoiceItem[];
} 