import { useState } from 'react';

const ChevronDownIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
);
const CheckIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
    </svg>
);
const SpinnerIcon = ({ className }: { className?: string }) => (
    <svg className={`animate-spin ${className}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
);


const AVAILABLE_COLUMNS = [
    // Table: weather_readings
    { id: 'weather_readings:date', label: 'Date' },
    { id: 'weather_readings:temperature', label: 'Temperature' },
    { id: 'weather_readings:feels_like', label: 'Feels Like' },
    { id: 'weather_readings:temperature_min', label: 'Min Temp' },
    { id: 'weather_readings:temperature_max', label: 'Max Temp' },
    { id: 'weather_readings:humidity', label: 'Humidity' },
    { id: 'weather_readings:pressure', label: 'Pressure' },
    { id: 'weather_readings:wind_speed', label: 'Wind Speed' },
    { id: 'weather_readings:wind_deg', label: 'Wind Degrees' },
    { id: 'weather_readings:main', label: 'Condition (Main)' },
    { id: 'weather_readings:description', label: 'Condition (Desc)' },

    // Table: cities
    { id: 'cities:name', label: 'City Name' },
    { id: 'cities:latitude', label: 'Latitude' },
    { id: 'cities:longitude', label: 'Longitude' },

    // Table: countries
    { id: 'countries:common_name', label: 'Country Name' },
    { id: 'countries:iso2_code', label: 'ISO Code (2)' },
    { id: 'countries:iso3_code', label: 'ISO Code (3)' },
    { id: 'countries:region', label: 'Region' },
    { id: 'countries:subregion', label: 'Subregion' }
];

interface ExportFormProps {
    onDataFetched: (csvText: string, fileName: string) => void;
}

export default function ExportForm({ onDataFetched }: ExportFormProps) {
    const [fileName, setFileName] = useState<string>('');
    const [selectedCols, setSelectedCols] = useState<string[]>([]);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    const toggleColumn = (colId: string) => {
        setSelectedCols(prev =>
            prev.includes(colId) ? prev.filter(id => id !== colId) : [...prev, colId]
        );
    };

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus('loading');
        setErrorMessage('');

        try {
            const payload = {
                name: fileName || "unknown",
                columns: selectedCols.length > 0 ? selectedCols : ["*"]
            };

            const initialResponse = await fetch(import.meta.env.VITE_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': import.meta.env.VITE_API_KEY
                },
                body: JSON.stringify(payload)
            });

            const data = await initialResponse.json();

            if (!initialResponse.ok) throw new Error(data.error || 'Failed to generate report');
            if (!data.download_link) throw new Error("API returned success but no download link.");

            const fileResponse = await fetch(data.download_link);
            if (!fileResponse.ok) throw new Error("Failed to download the generated CSV file.");

            const csvText = await fileResponse.text();

            onDataFetched(csvText, fileName);

            setStatus('success');

        } catch (error: unknown) {
            console.error(error);
            setStatus('error');
            if (error instanceof Error) setErrorMessage(error.message);
        }
    };

    return (
        <form onSubmit={handleGenerate} className="w-full">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end bg-white dark:bg-zinc-900 p-4 rounded-xl border border-slate-200 dark:border-zinc-800 shadow-sm">
                <div className="md:col-span-4 space-y-1.5">
                    <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                        File Name <span className="font-normal normal-case text-slate-400 dark:text-zinc-500 ml-1">(Optional)</span>
                    </label>
                    <input
                        type="text"
                        placeholder="weather_export"
                        value={fileName}
                        onChange={(e) => setFileName(e.target.value)}
                        className="w-full px-3 py-2.5 bg-slate-50 dark:bg-black border border-slate-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 dark:text-white"
                    />
                </div>

                <div className="md:col-span-5 relative space-y-1.5">
                    <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Columns</label>
                    <button
                        type="button"
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                        className="w-full text-left px-3 py-2.5 border border-slate-200 dark:border-zinc-700 rounded-lg bg-slate-50 dark:bg-black flex justify-between items-center text-sm focus:ring-2 focus:ring-indigo-500 dark:text-white"
                    >
                        <span className="truncate">{selectedCols.length === 0 ? "All Columns" : `${selectedCols.length} Selected`}</span>
                        <ChevronDownIcon className="w-4 h-4 opacity-50" />
                    </button>
                    {isDropdownOpen && (
                        <>
                            <div className="fixed inset-0 z-10" onClick={() => setIsDropdownOpen(false)} />
                            <div className="absolute top-full mt-1 left-0 w-full z-20 bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                                {AVAILABLE_COLUMNS.map((col) => (
                                    <div key={col.id} onClick={() => toggleColumn(col.id)} className={`flex items-center justify-between px-3 py-2 text-sm cursor-pointer ${selectedCols.includes(col.id) ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-700'}`}>
                                        {col.label}
                                        {selectedCols.includes(col.id) && <CheckIcon className="w-4 h-4" />}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>

                <div className="md:col-span-3">
                    <button
                        type="submit"
                        disabled={status === 'loading'}
                        className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors flex justify-center items-center gap-2 disabled:opacity-70"
                    >
                        {status === 'loading' ? <SpinnerIcon className="w-4 h-4" /> : 'Generate CSV'}
                    </button>
                </div>
            </div>

            {status === 'error' && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg border border-red-200 dark:border-red-800/30">
                    Error: {errorMessage}
                </div>
            )}
        </form>
    );
}