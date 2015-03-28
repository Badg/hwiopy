import json, csv

# Get the damn files
with open('sitara_termmodes.json') as jsonfile:
    termmodes = json.load(jsonfile)
with open('Default pinmux.txt') as txtfile:
    pinmux = csv.DictReader(txtfile, fieldnames=['pinnum', 'address',
        'mux', 'driver', 'offset', 'reg name', 'pinname'])

    # Turn the pinmux file into a dict
    pinmux_dict = {}
    for row in pinmux:
        pinmux_dict[row['pinname']] = {}
        for key, value in row.items():
            if key != 'pinname':
                pinmux_dict[row['pinname']][key] = value

# Save the dict as a json
with open('sitara_pinmux.json', 'w+') as jsonfile:
    json.dump(pinmux_dict, jsonfile, indent=4)

# Carry on then
for key in termmodes:
    terminal_name = termmodes[key]['name'].lower()
    if terminal_name in pinmux_dict:
        termmodes[key]['kernel_number'] = pinmux_dict[terminal_name]['pinnum']
        termmodes[key]['control_reg_address'] = pinmux_dict[terminal_name]['address']
        termmodes[key]['mux_default'] = pinmux_dict[terminal_name]['mux']
        termmodes[key]['driver'] = pinmux_dict[terminal_name]['driver']
        termmodes[key]['control_reg_offset'] = pinmux_dict[terminal_name]['offset']
        termmodes[key]['control_reg_name'] = pinmux_dict[terminal_name]['reg name']
    else:
        if terminal_name[0] != 'v' and terminal_name[:3] != 'ddr':
            print('Missing: ' + terminal_name)

with open('sitara_termmodes2.json', 'w+') as jsonfile:
    json.dump(termmodes, jsonfile, indent=4)