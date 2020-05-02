#!/usr/bin/perl -l

my $infile = shift;
my $outfile = shift;
my @players;
my $buffer;
my $RANK_VERSION = 11;

die("Usage: ./statsed.pl <infile> [outfile]\n") unless $infile ne "";

open(INFILE, $infile) or die "File $infile could not be opened.\n";
binmode(INFILE);

if (!read(INFILE, $buffer, 2)) {
    die "File $infile looks like an invalid file.\n";
    close(INFILE);
}

my $vers = unpack("s1", $buffer);
if ($vers != $RANK_VERSION) {
    print "File $infile does not have the correct header version ($RANK_VERSION)\n";
    die("Detected version: $vers\n");
}

if (!read(INFILE, $buffer, 2)) {
    die "File $infile looks malformed.\n";
}

my $bytes = unpack("S1", $buffer);
my $num = 0;
my $str = "";
my @stats;

#INPUT FILE
while ($bytes) {
    read(INFILE, $buffer, $bytes);
    $players[$num]->{name} = unpack("Z*", $buffer);

    read(INFILE, $buffer, 2);
    $bytes = unpack("S1", $buffer);
    read(INFILE, $buffer, $bytes);
    $players[$num]->{auth} = unpack("Z*", $buffer);

    read(INFILE, $buffer, 11 * 4);
    @stats = unpack("L11", $buffer);
    $players[$num]->{tks} = $stats[0];
    $players[$num]->{damage} = $stats[1];
    $players[$num]->{deaths} = $stats[2];
    $players[$num]->{kills} = $stats[3];
    $players[$num]->{shots} = $stats[4];
    $players[$num]->{hits} = $stats[5];
    $players[$num]->{hs} = $stats[6];
    $players[$num]->{defuses} = $stats[7];
    $players[$num]->{defuse_attempts} = $stats[8];
    $players[$num]->{plants} = $stats[9];
    $players[$num]->{explosions} = $stats[10];

    read(INFILE, $buffer, 9 * 4);
    @{$players[$num]->{hits}} = unpack("L9", $buffer);

    read(INFILE, $buffer, 2);
    $bytes = unpack("S1", $buffer);

    $num++;
}

close(INFILE);

print '<table id="statsTable" class="display" style="width:50%"><thead>
<tr>
<th>Name</th>
<th>Kills</th>
<th>Deaths</th>
<th>Hits</th>
<th>Shots</th>
<th>Headshots</th>
<th>Score (kills-deaths)</th>
<th>Accuracy (hits/shots)</th>
<th>Lethality (kills/shots)</th>
<th>Aim (headshots/hits)</th>
<th>Bombs defused</th>
<th>Explosions caused</th>
<th>Yuta level</th>
</tr>
</thead><tbody>';

for ($i = 0; $i <= $#players; $i++) {
    my %player = %{$players[$i]};
    my @stats = @{$player{hits}};
    if ($player{shots} > 0) {
        $player{lethality} = sprintf("%.3f", $player{kills} / $player{shots});
    }
    if ($player{shots} > 0) {
        $player{accuracy} = sprintf("%.3f", $player{hits} / $player{shots});
    }
    if ($player{hits} > 0) {
        $player{hsratio} = sprintf("%.3f", $player{hs} / $player{hits});
    }
    $player{yuta} = $player{defuses} - $player{explosions};

    $player{score} = $player{kills} - $player{deaths};
    $player{rank} = $i + 1;

    print '<tr>';
    print "
    <td>" . $player{name} . "</td>
    <td>" . $player{kills} . "</td>
    <td>" . $player{deaths} . "</td>
    <td>" . $player{hits} . "</td>
    <td>" . $player{shots} . "</td>
    <td>" . $player{hs} . "</td>
    <td>" . $player{score} . "</td>
    <td>" . $player{accuracy} . "</td>
    <td>" . $player{lethality} . "</td>
    <td>" . $player{hsratio} . "</td>
    <td>" . $player{defuses} . "</td>
    <td>" . $player{explosions} . "</td>
    <td>" . $player{yuta} . "</td>
    ";
    print '</tr>';
}
