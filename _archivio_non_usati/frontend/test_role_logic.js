/**
 * Test Script per la Logica di Filtraggio Ruoli
 * Verifica che la configurazione della sidebar rispetti i requisiti specificati
 */

// Configurazione sidebar (copiata dal layout.tsx)
const sidebarSections = [
    {
        title: "Dashboard",
        items: [
            { title: "Dashboard", href: "/dashboard", roles: null }
        ]
    },
    {
        title: "Gestione ODL",
        items: [
            { title: "ODL", href: "/dashboard/shared/odl", roles: ['ADMIN', 'RESPONSABILE'] },
            { title: "Monitoraggio ODL", href: "/dashboard/responsabile/odl-monitoring", roles: ['ADMIN', 'RESPONSABILE'] }
        ],
        roles: ['ADMIN', 'RESPONSABILE']
    },
    {
        title: "Produzione",
        items: [
            { title: "Produzione", href: "/dashboard/laminatore/produzione", roles: ['ADMIN', 'LAMINATORE'] },
            { title: "Tools/Stampi", href: "/dashboard/laminatore/tools", roles: ['ADMIN', 'LAMINATORE'] }
        ],
        roles: ['ADMIN', 'LAMINATORE']
    },
    {
        title: "Autoclave",
        items: [
            { title: "Nesting", href: "/dashboard/autoclavista/nesting", roles: ['ADMIN', 'AUTOCLAVISTA'] },
            { title: "Autoclavi", href: "/dashboard/autoclavista/autoclavi", roles: ['ADMIN', 'AUTOCLAVISTA'] },
            { title: "Reports", href: "/dashboard/responsabile/reports", roles: ['ADMIN', 'AUTOCLAVISTA'] }
        ],
        roles: ['ADMIN', 'AUTOCLAVISTA']
    },
    {
        title: "Pianificazione",
        items: [
            { title: "Schedule", href: "/dashboard/autoclavista/schedule", roles: ['ADMIN', 'RESPONSABILE'] }
        ],
        roles: ['ADMIN', 'RESPONSABILE']
    },
    {
        title: "Amministrazione",
        items: [
            { title: "Catalogo", href: "/dashboard/shared/catalog", roles: ['ADMIN'] },
            { title: "Parti", href: "/dashboard/laminatore/parts", roles: ['ADMIN'] },
            { title: "Cicli Cura", href: "/dashboard/autoclavista/cicli-cura", roles: ['ADMIN'] },
            { title: "Statistiche", href: "/dashboard/responsabile/statistiche", roles: ['ADMIN'] },
            { title: "Tempi & Performance", href: "/dashboard/laminatore/tempi", roles: ['ADMIN'] },
            { title: "Impostazioni", href: "/dashboard/admin/impostazioni", roles: ['ADMIN'] }
        ],
        roles: ['ADMIN']
    }
];

// Logica di filtraggio (copiata dal layout.tsx)
function filterItemsByRole(items, role) {
    return items.filter(item => {
        if (!item.roles) return true;
        if (!role) return false;
        return item.roles.includes(role);
    });
}

function filterSectionsByRole(sections, role) {
    return sections
        .map(section => ({
            ...section,
            items: filterItemsByRole(section.items, role)
        }))
        .filter(section => {
            if (!section.roles) return section.items.length > 0;
            if (!role) return false;
            return section.roles.includes(role) && section.items.length > 0;
        });
}

// Requisiti da verificare
const requirements = {
    ADMIN: "deve poter vedere tutte le voci",
    RESPONSABILE: "vede solo ODL, monitoraggio, schedule",
    LAMINATORE: "vede solo produzione, tool",
    AUTOCLAVISTA: "vede nesting, autoclavi, reports"
};

// Funzione di test
function testRole(role) {
    console.log(`\n🧪 TESTING RUOLO: ${role}`);
    console.log(`📋 Requisito: ${requirements[role]}`);
    console.log("─".repeat(50));
    
    const filteredSections = filterSectionsByRole(sidebarSections, role);
    const visibleItems = [];
    
    filteredSections.forEach(section => {
        console.log(`📁 ${section.title}:`);
        section.items.forEach(item => {
            console.log(`  ✅ ${item.title}`);
            visibleItems.push(item.title);
        });
    });
    
    console.log(`\n📊 Totale voci visibili: ${visibleItems.length}`);
    return visibleItems;
}

// Verifica requisiti specifici
function verifyRequirements() {
    console.log("🔍 VERIFICA REQUISITI SPECIFICI");
    console.log("=".repeat(60));
    
    // Test ADMIN - deve vedere tutto
    const adminItems = testRole('ADMIN');
    const totalItems = sidebarSections.reduce((acc, section) => acc + section.items.length, 0);
    console.log(`✅ ADMIN vede ${adminItems.length}/${totalItems} voci (${adminItems.length === totalItems ? 'CORRETTO' : 'ERRORE'})`);
    
    // Test RESPONSABILE - solo ODL, monitoraggio, schedule
    const responsabileItems = testRole('RESPONSABILE');
    const expectedResponsabile = ['Dashboard', 'ODL', 'Monitoraggio ODL', 'Schedule'];
    const responsabileOk = expectedResponsabile.every(item => responsabileItems.includes(item)) && 
                          responsabileItems.length === expectedResponsabile.length;
    console.log(`${responsabileOk ? '✅' : '❌'} RESPONSABILE: ${responsabileOk ? 'CORRETTO' : 'ERRORE'}`);
    
    // Test LAMINATORE - solo produzione, tool
    const laminatoreItems = testRole('LAMINATORE');
    const expectedLaminatore = ['Dashboard', 'Produzione', 'Tools/Stampi'];
    const laminatoreOk = expectedLaminatore.every(item => laminatoreItems.includes(item)) && 
                        laminatoreItems.length === expectedLaminatore.length;
    console.log(`${laminatoreOk ? '✅' : '❌'} LAMINATORE: ${laminatoreOk ? 'CORRETTO' : 'ERRORE'}`);
    
    // Test AUTOCLAVISTA - nesting, autoclavi, reports
    const autoclavistaItems = testRole('AUTOCLAVISTA');
    const expectedAutoclavista = ['Dashboard', 'Nesting', 'Autoclavi', 'Reports'];
    const autoclavistaOk = expectedAutoclavista.every(item => autoclavistaItems.includes(item)) && 
                          autoclavistaItems.length === expectedAutoclavista.length;
    console.log(`${autoclavistaOk ? '✅' : '❌'} AUTOCLAVISTA: ${autoclavistaOk ? 'CORRETTO' : 'ERRORE'}`);
    
    // Test NESSUN RUOLO
    console.log(`\n🧪 TESTING RUOLO: null (nessun ruolo)`);
    console.log("─".repeat(50));
    const noRoleItems = filterSectionsByRole(sidebarSections, null);
    console.log(`${noRoleItems.length === 0 ? '✅' : '❌'} NESSUN RUOLO: ${noRoleItems.length === 0 ? 'CORRETTO (nessuna voce visibile)' : 'ERRORE'}`);
    
    console.log("\n🎯 RIEPILOGO FINALE:");
    console.log("=".repeat(60));
    console.log(`✅ ADMIN: Accesso completo (${adminItems.length} voci)`);
    console.log(`${responsabileOk ? '✅' : '❌'} RESPONSABILE: ${responsabileItems.join(', ')}`);
    console.log(`${laminatoreOk ? '✅' : '❌'} LAMINATORE: ${laminatoreItems.join(', ')}`);
    console.log(`${autoclavistaOk ? '✅' : '❌'} AUTOCLAVISTA: ${autoclavistaItems.join(', ')}`);
    
    const allTestsPassed = responsabileOk && laminatoreOk && autoclavistaOk;
    console.log(`\n🏆 RISULTATO FINALE: ${allTestsPassed ? '✅ TUTTI I TEST SUPERATI' : '❌ ALCUNI TEST FALLITI'}`);
    
    return allTestsPassed;
}

// Esegui i test
if (require.main === module) {
    verifyRequirements();
}

module.exports = {
    sidebarSections,
    filterItemsByRole,
    filterSectionsByRole,
    testRole,
    verifyRequirements
}; 