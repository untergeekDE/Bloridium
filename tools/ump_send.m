// ump_send: Sendet UMP/MIDI-Pakete an einen CoreMIDI-Destination-Port.
// Aufruf: ump_send <destName> <hexPacket> [hexPacket...]
//   z.B.: ump_send "MIDI 2.0" "40 90 3C 00 FF FF 00 00"
#import <CoreMIDI/CoreMIDI.h>
#import <CoreFoundation/CoreFoundation.h>
#import <Foundation/Foundation.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: ump_send <destName> <hexPacket>...\n");
        return 1;
    }
    NSString *destName = [NSString stringWithUTF8String:argv[1]];
    int npackets = argc - 2;

    MIDIEndpointRef dest = 0;
    for (CFIndex i = 0; i < MIDIGetNumberOfDestinations(); i++) {
        MIDIEndpointRef ep = MIDIGetDestination(i);
        CFStringRef name = NULL;
        MIDIObjectGetStringProperty(ep, kMIDIPropertyName, &name);
        if (name && CFStringCompare(name, (__bridge CFStringRef)destName, 0) == kCFCompareEqualTo) {
            dest = ep;
        }
        if (name) CFRelease(name);
    }
    if (!dest) {
        fprintf(stderr, "destination nicht gefunden: %s\n", argv[1]);
        return 2;
    }

    MIDIClientRef client = 0;
    OSStatus err = MIDIClientCreate(CFSTR("ump-send"), NULL, NULL, &client);
    MIDIPortRef port = 0;
    err |= MIDIOutputPortCreate(client, CFSTR("out"), &port);
    if (err) { fprintf(stderr, "client/port error %d\n", (int)err); return 3; }

    // Pakete parsen
    ByteCount listSize = sizeof(MIDIPacketList) + (npackets - 1) * sizeof(MIDIPacket);
    MIDIPacketList *pktlist = (MIDIPacketList *)calloc(1, listSize);
    MIDIPacketListInit(pktlist);
    MIDIPacket *cur = pktlist->packet;
    for (int k = 0; k < npackets; k++) {
        const char *hex = argv[2 + k];
        UInt8 data[256];
        int len = 0;
        const char *p = hex;
        while (*p && len < 256) {
            while (*p == ' ') p++;
            if (!*p) break;
            char byteStr[3] = {p[0], p[1], 0};
            data[len++] = (UInt8)strtoul(byteStr, NULL, 16);
            p += 2;
        }
        cur = MIDIPacketListAdd(pktlist, listSize, cur, 0, (UInt16)len, data);
    }
    err = MIDISend(port, dest, pktlist);
    printf("sent %u packet(s) to '%s', err=%d\n", pktlist->numPackets, argv[1], (int)err);
    free(pktlist);
    return err == 0 ? 0 : 4;
}
