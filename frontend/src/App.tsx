import { useState, useEffect } from 'react';
import ExportForm from './components/ExportForm';

const SunIcon = () => (
    <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
);
const MoonIcon = () => (
    <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
    </svg>
);
const EyeIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
);
const SaveIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
    </svg>
);

function App() {
    const [darkMode, setDarkMode] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('theme') === 'dark' ||
                (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
        }
        return false;
    });

    const [csvData, setCsvData] = useState<string | null>(null);
    const [fileName, setFileName] = useState<string | null>(null);

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('theme', darkMode ? 'dark' : 'light');
    }, [darkMode]);

    const handleDownloadFile = () => {
        if (!csvData) return;
        const blob = new Blob([csvData], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${fileName}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    };

    const getAllRows = () => {
        if (!csvData) return [];
        const lines = csvData.split('\n').filter(line => line.trim() !== '');
        return lines.map(line => line.split(','));
    };

    const allRows = getAllRows();

    return (
        <div className="min-h-screen w-full bg-slate-50 dark:bg-zinc-950 text-slate-900 dark:text-slate-100 transition-colors duration-300">

            <div className="max-w-5xl mx-auto px-4 py-8">
                <header className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold tracking-tight">Weather Data Pipeline</h1>
                    <button
                        onClick={() => setDarkMode(!darkMode)}
                        className="p-2 rounded-full bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm hover:shadow-md transition-all"
                    >
                        {darkMode ? <SunIcon /> : <MoonIcon />}
                    </button>
                </header>

                <div className="mb-6">
                    <ExportForm onDataFetched={(data, fileName) => {
                        setCsvData(data);
                        setFileName(fileName);
                    }} />
                </div>

                {csvData ? (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">

                        <div className="flex justify-between items-center mb-3">
                            <h3 className="text-sm font-semibold text-slate-600 dark:text-slate-400 flex items-center gap-2">
                                <EyeIcon className="w-4 h-4" />
                                Previewing {Math.min(allRows.length - 1, 250)} Records
                            </h3>
                            <button
                                onClick={handleDownloadFile}
                                className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all shadow-md hover:shadow-lg"
                            >
                                <SaveIcon className="w-4 h-4" />
                                Download CSV
                            </button>
                        </div>

                        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-zinc-800 shadow-sm bg-white dark:bg-zinc-900 max-h-[600px] overflow-y-auto">
                            <table className="w-full text-sm text-left text-slate-600 dark:text-slate-300">
                                <thead className="text-xs text-slate-700 uppercase bg-slate-100 dark:bg-zinc-800 dark:text-slate-200 sticky top-0">
                                    <tr>
                                        {allRows[0]?.map((header, i) => (
                                            <th key={i} className="px-6 py-4 whitespace-nowrap bg-slate-100 dark:bg-zinc-800">{header}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-200 dark:divide-zinc-800">
                                {allRows.slice(1, 251).map((row, rowIndex) => (
                                    <tr key={rowIndex} className="hover:bg-slate-50 dark:hover:bg-zinc-800/50 transition-colors">
                                        {row.map((cell, cellIndex) => (
                                            <td key={cellIndex} className="px-6 py-4 whitespace-nowrap font-mono text-xs">
                                                {cell}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>

                    </div>
                ) : (
                    <div className="w-full h-64 bg-white dark:bg-zinc-900 rounded-lg border border-dashed border-slate-300 dark:border-zinc-700 flex flex-col items-center justify-center text-slate-400 gap-2">
                        <p>[ Table Data Will Go Here ]</p>
                        <p className="text-xs opacity-50">Select columns and click Generate CSV to preview</p>
                    </div>
                )}

            </div>
        </div>
    );
}

export default App;